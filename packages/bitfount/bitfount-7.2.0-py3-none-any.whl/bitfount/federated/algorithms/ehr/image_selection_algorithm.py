"""For selection of images related to patients for upload."""

from collections import defaultdict
from typing import Any, ClassVar, Optional

from bitfount.data.datasources.base_source import BaseSource
from bitfount.data.datasources.utils import ORIGINAL_FILENAME_METADATA_COLUMN
from bitfount.data.datasplitters import DatasetSplitter
from bitfount.data.datastructure import DataStructure
from bitfount.federated.algorithms.base import (
    BaseNonModelAlgorithmFactory,
    BaseWorkerAlgorithm,
    NoResultsModellerAlgorithm,
)
from bitfount.federated.algorithms.ophthalmology.ophth_algo_types import PATIENT_ID_COL
from bitfount.federated.exceptions import AlgorithmError
from bitfount.federated.logging import _get_federated_logger
from bitfount.federated.privacy.differential import DPPodConfig
from bitfount.federated.types import ProtocolContext
from bitfount.types import T_FIELDS_DICT

_logger = _get_federated_logger("bitfount.federated")


class _WorkerSide(BaseWorkerAlgorithm):
    """Worker side of the algo for selecting images related to a patient."""

    def __init__(
        self,
        **kwargs: Any,
    ) -> None:
        """Initialize the worker-side algorithm.

        Args:
            patient_ids: List of patient IDs to get images for.
            **kwargs: Additional keyword arguments.
        """
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
        patient_ids: list[str],
    ) -> dict[str, list[str]]:
        """Returns list of files related to patient IDs.

        Args:
            patient_ids: List of patient ids to identify files for.
        """
        # Iterate through items in datasource, check if patient ID in list
        # Return dict of patient ID to list of files for them

        files_to_upload: dict[str, list[str]] = defaultdict(list)

        patient_id_column = None

        for data in self.datasource.yield_data():
            if ORIGINAL_FILENAME_METADATA_COLUMN not in data.columns:
                raise AlgorithmError(
                    f"Missing {ORIGINAL_FILENAME_METADATA_COLUMN}"
                    f" column in data to determine which images"
                    f" to upload."
                )

            if patient_id_column is None:
                if PATIENT_ID_COL in data.columns:
                    patient_id_column = PATIENT_ID_COL
                elif "patient_key" in data.columns:
                    patient_id_column = (
                        "patient_key"  # Heidelberg would use patient_key
                    )
                else:
                    _logger.info(
                        f"Unable to find patient ID column in data: {data.columns}"
                    )
                    raise AlgorithmError(
                        "Unable to find matching records as "
                        "patient ID is not present in data"
                    )

            matching_patient_rows = data[
                data[patient_id_column].apply(lambda pid: pid in patient_ids)
            ]

            if len(matching_patient_rows) == 0:
                continue

            id_to_filename_df = matching_patient_rows[
                [patient_id_column, ORIGINAL_FILENAME_METADATA_COLUMN]
            ]
            filenames_agg = id_to_filename_df.groupby(patient_id_column).aggregate(list)
            result = filenames_agg.to_dict()[ORIGINAL_FILENAME_METADATA_COLUMN]

            for patient_id, filenames in result.items():
                files_to_upload[patient_id].extend(filenames)

        return files_to_upload


class ImageSelectionAlgorithm(
    BaseNonModelAlgorithmFactory[NoResultsModellerAlgorithm, _WorkerSide]
):
    """Algorithm for selecting images related to a patient."""

    fields_dict: ClassVar[T_FIELDS_DICT] = {}

    def __init__(
        self,
        datastructure: DataStructure,
        **kwargs: Any,
    ) -> None:
        """Initialize the algorithm.

        Args:
            datastructure: The data structure definition
            patient_ids: The patients for whom to identify a list of images.
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
            log_message="Running Image Selection Algorithm",
            **kwargs,
        )

    def worker(
        self,
        *,
        context: Optional[ProtocolContext] = None,
        **kwargs: Any,
    ) -> _WorkerSide:
        """Worker-side of the algorithm."""
        return _WorkerSide(
            **kwargs,
        )
