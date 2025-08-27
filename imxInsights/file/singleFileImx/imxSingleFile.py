import warnings
from pathlib import Path

from loguru import logger

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSingleFileMetadata import SingleImxMetadata
from imxInsights.file.singleFileImx.imxSituation import ImxSituation
from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol


class ImxSingleFile:
    """
    Represents an IMX file that contains project situations or just a situation.

    Args:
        imx_file_path: Path to the IMX container.

    Attributes:
        file: The IMX file.
        situation: The IMX Situation.
        new_situation: The IMX NewSituation.
        initial_situation: The IMX InitialSituation.

    """

    def __init__(self, imx_file_path: Path | str):
        imx_file_path = Path(imx_file_path)
        warnings.warn(
            "Support for SingleImx (IMX version pre 12.0.0) will be dropped in December 2025. ",
            DeprecationWarning,
            stacklevel=2,
        )
        logger.info(f"processing {imx_file_path.name}")
        self.file: ImxFile = ImxFile(imx_file_path=imx_file_path)
        self.situation: ImxSituationProtocol | None = None
        self.new_situation: ImxSituationProtocol | None = None
        self.initial_situation: ImxSituationProtocol | None = None
        self.project_metadata: SingleImxMetadata | None = None
        self._populate_project_metadata()

        for situation_type, attribute_name in [
            ("Situation", "situation"),
            ("InitialSituation", "initial_situation"),
            ("NewSituation", "new_situation"),
        ]:
            if self.file.root is not None:
                situation = self.file.root.find(
                    f".//{{http://www.prorail.nl/IMSpoor}}{situation_type}"
                )
                if situation is not None:
                    imx_situation = ImxSituation(
                        imx_file_path, situation, self.file, self.project_metadata
                    )
                    setattr(self, attribute_name, imx_situation)

        self._classify_ares()

        logger.success(f"finished processing {self.file.path.name}")

    def _populate_project_metadata(self):
        self.project_metadata = SingleImxMetadata.from_element(self.file.root)

    def _classify_ares(self):
        if self.project_metadata:
            area_classifier = self.project_metadata.get_area_classifier()

            if self.situation:
                self.situation.classify_areas(area_classifier)
            if self.new_situation:
                self.new_situation.classify_areas(area_classifier)
            if self.initial_situation:
                self.initial_situation.classify_areas(area_classifier)
