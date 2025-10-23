"""NextGen Patient Info download algorithm to access patient data.

This module implements an algorithm for downloading all patient information
from NextGen's APIs. It provides functionality to:
- Authenticate with NextGen's FHIR, Enterprise, and SMART on FHIR APIs
- Look up and download relevant info and documents for a given list of patient_ids
"""

from collections import defaultdict
from pathlib import Path
from typing import Any, ClassVar, Optional

from bitfount.data.datastructure import DataStructure
from bitfount.externals.ehr.nextgen.authentication import NextGenAuthSession
from bitfount.externals.ehr.nextgen.querier import NextGenPatientQuerier
from bitfount.federated.algorithms.base import (
    BaseNonModelAlgorithmFactory,
    NoResultsModellerAlgorithm,
)
from bitfount.federated.algorithms.ehr.ehr_base_algorithm import (
    BaseEHRWorkerAlgorithm,
    QuerierType,
)
from bitfount.federated.logging import _get_federated_logger
from bitfount.federated.types import ProtocolContext
from bitfount.hub.api import (
    BitfountHub,
    SMARTOnFHIR,
)
from bitfount.hub.authentication_flow import (
    BitfountSession,
)
from bitfount.types import T_FIELDS_DICT

_logger = _get_federated_logger("bitfount.federated")


class _WorkerSide(BaseEHRWorkerAlgorithm):
    """Worker side of the algorithm for downloading patient info using NextGen."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize the worker-side algorithm.

        Args:
            session: BitfountSession object for use with SMARTOnFHIR service. Will be
                created if not provided.
            **kwargs: Additional keyword arguments.
        """
        super().__init__(**kwargs)

    def run(
        self,
        patient_ids: list[str],
        download_path: Path,
        run_document_download: bool = True,
        run_json_dump: bool = True,
    ) -> dict[str, list[Path]]:
        """Download relevant info and documents related to supplied list of patients.

        Args:
            patient_ids: List of patient ids to download data for.
            download_path: Local path to save the downloaded patient info.
            run_document_download: Boolean flag to turn on/off document downloads,
                downloads documents by default.
            run_json_dump: Boolean flag to turn on/off patient info JSON dump,
                does the JSON dump by default.

        Returns:
            dictionary of patient_id string to list of paths of downloaded files
             related to that patient
        """
        if self.querier_type == QuerierType.NEXTGEN:
            files_to_upload = self._run_for_nextgen(
                patient_ids, download_path, run_document_download, run_json_dump
            )
        else:
            raise NotImplementedError(
                "Download mechanism has not been implemented yet for this EHR system."
            )

        return files_to_upload

    def _run_for_nextgen(
        self,
        patient_ids: list[str],
        download_path: Path,
        run_document_download: bool = True,
        run_json_dump: bool = True,
    ) -> dict[str, list[Path]]:
        """Download files with NextGen EHR."""
        # Get SMART on FHIR bearer token
        smart_auth = SMARTOnFHIR(
            session=self.session,
            smart_on_fhir_url=self.smart_on_fhir_url,
            resource_server_url=self.smart_on_fhir_resource_server_url,
        )
        nextgen_session = NextGenAuthSession(smart_auth)

        files_to_upload: dict[str, list[Path]] = defaultdict(list)

        # Process each patient
        num_patient_ids = len(patient_ids)
        for i, patient_id in enumerate(patient_ids, start=1):
            _logger.info(f"Running EHR extraction for patient {i} of {num_patient_ids}")
            nextgen_querier = NextGenPatientQuerier.from_nextgen_session(
                patient_id=patient_id,
                nextgen_session=nextgen_session,
                fhir_url=self.fhir_url,
                enterprise_url=self.enterprise_url,  # type:ignore[arg-type] # Reason: would have been set during initialise #noqa:E501
            )

            # Create directory for patient document download
            patient_folder_path = download_path / patient_id
            patient_folder_path.mkdir(parents=True, exist_ok=True)
            _logger.debug(
                f"Created output dir for patient {patient_id}"
                f" at {str(patient_folder_path)}"
            )

            if run_document_download:
                _logger.info(
                    f"Downloading documents for patient {i} of {num_patient_ids}"
                )
                downloaded_docs = nextgen_querier.download_all_documents(
                    save_path=patient_folder_path
                )

                files_to_upload[patient_id].extend(downloaded_docs)

            if run_json_dump:
                _logger.info(
                    f"Downloading JSON entries for patient {i} of {num_patient_ids}"
                )
                nextgen_querier.produce_json_dump(
                    save_path=patient_folder_path / "patient_info.json"
                )
                files_to_upload[patient_id].append(
                    patient_folder_path / "patient_info.json",
                )

        return files_to_upload


class EHRPatientInfoDownloadAlgorithm(
    BaseNonModelAlgorithmFactory[NoResultsModellerAlgorithm, _WorkerSide]
):
    """Algorithm for downloading patient info and documents from EHR."""

    # DEV: This is set so that the algorithm/encapsulating protocol won't try to use
    #      the `processed_files_cache` as the context for this algorithm is that it
    #      will be running in a protocol that just receives a list of patient IDs,
    #      doesn't interact with the datasource.
    _inference_algorithm = False

    fields_dict: ClassVar[T_FIELDS_DICT] = {}

    def __init__(
        self,
        datastructure: DataStructure,
        **kwargs: Any,
    ) -> None:
        """Initialize the algorithm.

        Args:
            datastructure: The data structure definition
            **kwargs: Additional keyword arguments.
        """
        super().__init__(datastructure=datastructure, **kwargs)

    def modeller(
        self,
        *,
        context: Optional[ProtocolContext] = None,
        **kwargs: Any,
    ) -> NoResultsModellerAlgorithm:
        """Modeller-side of the algorithm."""
        return NoResultsModellerAlgorithm(
            log_message="Running EHR Patient Info Download Algorithm",
            **kwargs,
        )

    def worker(
        self,
        *,
        hub: Optional[BitfountHub] = None,
        session: Optional[BitfountSession] = None,
        context: Optional[ProtocolContext] = None,
        **kwargs: Any,
    ) -> _WorkerSide:
        """Worker-side of the algorithm."""
        if hub is None and session is None:
            raise ValueError("One of hub or session must be provided.")

        session_: BitfountSession
        if hub is not None and session is not None:
            _logger.warning(
                "Both hub and session were provided;"
                " using provided session in preference to hub session."
            )
            session_ = session
        elif hub is not None:
            session_ = hub.session
        else:  # session is not None
            assert session is not None  # nosec[assert_used]: Previous checks guarantee this is not None here # noqa: E501
            session_ = session

        return _WorkerSide(
            session=session_,
            **kwargs,
        )
