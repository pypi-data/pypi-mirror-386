"""Algorithm for uploading documents to an AWS S3 bucket."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, ClassVar, Optional, cast

from requests import HTTPError, RequestException

from bitfount.data.datasources.base_source import (
    BaseSource,
)
from bitfount.data.datasplitters import DatasetSplitter
from bitfount.data.datastructure import DataStructure
from bitfount.federated.algorithms.base import (
    BaseModellerAlgorithm,
    BaseNonModelAlgorithmFactory,
    BaseWorkerAlgorithm,
)
from bitfount.federated.exceptions import AlgorithmError
from bitfount.federated.logging import _get_federated_logger
from bitfount.federated.privacy.differential import DPPodConfig
from bitfount.storage import _upload_file_to_s3
from bitfount.types import T_FIELDS_DICT, _S3PresignedPOSTFields, _S3PresignedPOSTURL
from bitfount.utils.aws_utils import AWSError, get_boto_session

logger = _get_federated_logger(__name__)

S3_UPLOAD_RETRY_ATTEMPTS = 3

DEFAULT_URL_EXPIRY_IN_SECONDS = 10800  # 3 hours


class _ModellerSide(BaseModellerAlgorithm):
    """Modeller side of the S3Upload algorithm."""

    def __init__(
        self,
        s3_bucket: Optional[str],
        aws_region: Optional[str] = None,
        aws_profile: str = "default",
        **kwargs: Any,
    ):
        """Init method for the Modeller side of S3 Upload Algo.

        Args:
            s3_bucket: Name of S3 bucket to upload into.
            aws_region: AWS region in which the bucket resides.
            aws_profile: Name of AWS profile with which to generate the
              pre-signed POST.
            kwargs: Additional args to pass to the base class.
        """
        super().__init__(**kwargs)

        # Env var for AWS region will override argument
        if os.getenv("AWS_REGION"):
            aws_region = os.getenv("AWS_REGION")

        if any(param is None for param in [s3_bucket, aws_region]):
            null_params = []
            if s3_bucket is None:
                null_params.append("s3_bucket")
            if aws_region is None:
                null_params.append("aws_region")

            raise AlgorithmError(
                f"Required params not set on the S3UploadAlgorithm Modeller:"
                f" {null_params}"
            )

        self.s3_bucket: str = s3_bucket  # type:ignore[assignment]
        self.aws_profile: str = aws_profile
        self.aws_region: str = aws_region  # type:ignore[assignment]

    def run(
        self,
        subdirectory_for_upload: str,
        url_expiry_in_seconds: int = DEFAULT_URL_EXPIRY_IN_SECONDS,
    ) -> tuple[_S3PresignedPOSTURL, _S3PresignedPOSTFields]:
        """Provides the S3 presigned URL to worker.

        Args:
            subdirectory_for_upload: Limit the generated presigned POST
              to only uploads within this bucket key.
            url_expiry_in_seconds: Amount of time the generated pre-signed
              POST url will last for before expiring.
        """
        # Remove any extra slashes
        subdirectory_for_upload = subdirectory_for_upload.strip("/")

        try:
            session = get_boto_session(aws_profile=self.aws_profile)
        except AWSError as e:
            raise AlgorithmError(
                "No credentials provided in environment variables,"
                " and no aws_profile set."
            ) from e

        s3_client = session.client("s3", region_name=self.aws_region)
        presigned_url = s3_client.generate_presigned_post(
            Bucket=self.s3_bucket,
            Key=f"{subdirectory_for_upload}/${{filename}}",  # limits any uploads to this subdirectory  #noqa: E501
            ExpiresIn=url_expiry_in_seconds,
            Conditions=[["starts-with", "$key", f"{subdirectory_for_upload}/"]],
        )

        logger.info(
            f"Modeller generated pre-signed POST for"
            f" worker for bucket: {self.s3_bucket}"
        )

        return presigned_url["url"], presigned_url["fields"]

    def initialise(
        self,
        task_id: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Nothing to initialise here."""
        pass


class _WorkerSide(BaseWorkerAlgorithm):
    """Worker side of the algorithm."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)

    def initialise(
        self,
        datasource: BaseSource,
        data_splitter: Optional[DatasetSplitter] = None,
        pod_dp: Optional[DPPodConfig] = None,
        pod_identifier: Optional[str] = None,
        **kwargs: Any,
    ) -> None:
        """Sets Datasource."""
        self.initialise_data(datasource=datasource, data_splitter=data_splitter)

    def run(
        self,
        files_to_upload: dict[str | Path, str],
        presigned_url: _S3PresignedPOSTURL,
        presigned_fields: _S3PresignedPOSTFields,
        retry_attempts: int = S3_UPLOAD_RETRY_ATTEMPTS,
    ) -> dict[str | Path, str]:
        """Uploads a list of files to a bucket.

        Args:
            files_to_upload: dict of local paths of files to be uploaded,
              to desired uploaded S3 key+filename for this file.
              If desired file name is an empty string, will upload as
              local file name.
            presigned_url: Pre-signed URL received from modeller.
            presigned_fields: Pre-signed fields for uploading file.
            retry_attempts: Number of retry attempts for a failed upload.

        Returns:
            A dictionary of file names that were successfully uploaded.
        """
        current_upload_dict = files_to_upload
        current_attempt = 1

        failed_files = {}
        successful_files = {}
        skipped_files = []

        subdirectory_for_upload = presigned_fields["key"].replace("/${filename}", "")

        while current_attempt <= retry_attempts and current_upload_dict:
            logger.info(
                f"Uploading files (attempt {current_attempt} of"
                f" {retry_attempts}):"
                f" uploading {len(current_upload_dict)} file(s)."
            )

            for file_name, upload_name in current_upload_dict.items():
                if not os.path.exists(file_name):
                    logger.warning(f"{file_name} does not exist, skipping.")
                    skipped_files.append(file_name)
                    continue

                if not upload_name:
                    upload_name = Path(file_name).name
                elif (
                    "." not in upload_name.split("/")[-1]
                ):  # a directory is provided instead of file name
                    upload_name = (Path(upload_name) / Path(file_name).name).as_posix()

                full_upload_path: str = (
                    Path(subdirectory_for_upload) / upload_name
                ).as_posix()

                upload_presigned_fields: _S3PresignedPOSTFields = cast(
                    _S3PresignedPOSTFields, presigned_fields.copy()
                )
                upload_presigned_fields["key"] = full_upload_path

                try:
                    _upload_file_to_s3(
                        upload_url=presigned_url,
                        presigned_fields=upload_presigned_fields,
                        file_path=file_name,
                    )
                except HTTPError as e:
                    logger.error(f"Encountered error uploading file {file_name}: {e}")
                    failed_files[file_name] = upload_name
                except RequestException as e:
                    logger.error(f"Encountered error uploading file {file_name}: {e}")
                    failed_files[file_name] = upload_name
                else:
                    logger.info(
                        f"Successfully uploaded file {file_name} to bucket,"
                        f" s3 key: {full_upload_path}"
                    )
                    successful_files[file_name] = full_upload_path

            current_upload_dict = failed_files
            failed_files = {}
            current_attempt += 1

        if current_upload_dict:
            logger.info(
                f"Failed to upload {len(current_upload_dict)} files"
                f" after maximum retries ({retry_attempts}):"
                f" {list(current_upload_dict.keys())}"
            )
        if skipped_files:
            logger.info(f"Skipped {len(skipped_files)} missing files: {skipped_files}")

        logger.info(f"Successfully uploaded {len(successful_files)} file(s).")

        return successful_files


class S3UploadAlgorithm(BaseNonModelAlgorithmFactory[_ModellerSide, _WorkerSide]):
    """Algorithm for uploading files to S3.

    Args:
        datastructure: The data structure to use for the algorithm.
        s3_bucket: AWS S3 Bucket name to upload files into.
        aws_region: AWS region in which the bucket resides.
        aws_profile: Name of AWS profile with which to generate the
          pre-signed POST.
    """

    fields_dict: ClassVar[T_FIELDS_DICT] = {}

    def __init__(
        self,
        datastructure: DataStructure,
        s3_bucket: Optional[str] = None,
        aws_region: Optional[str] = None,
        aws_profile: str = "default",
        **kwargs: Any,
    ) -> None:
        super().__init__(datastructure=datastructure, **kwargs)
        self.s3_bucket = s3_bucket
        self.aws_region = aws_region
        self.aws_profile = aws_profile

    def modeller(self, **kwargs: Any) -> _ModellerSide:
        """Modeller-side of the algorithm."""
        return _ModellerSide(
            s3_bucket=self.s3_bucket,
            aws_profile=self.aws_profile,
            aws_region=self.aws_region,
            **kwargs,
        )

    def worker(self, **kwargs: Any) -> _WorkerSide:
        """Worker-side of the algorithm."""
        return _WorkerSide(
            **kwargs,
        )
