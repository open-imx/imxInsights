from datetime import datetime
from pathlib import Path

from loguru import logger
from lxml.etree import QName
from lxml.etree import _Element as Element

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSingleFileMetadata import SingleImxMetadata
from imxInsights.file.singleFileImx.imxSituationEnum import ImxSituationEnum
from imxInsights.repo.imxRepo import ImxRepo

# from imxInsights.report.singleImxPandasGenerator import SingleImxPandasGenerator
from imxInsights.utils.xml_helpers import parse_date


class ImxSituation(ImxRepo):
    """
    Represents a IMX Situation.
    """

    def __init__(
        self,
        imx_file_path: Path,
        situation_element: Element,
        imx_file: ImxFile,
        project_metadata: SingleImxMetadata | None,
    ):
        super().__init__(imx_file_path)
        logger.info(f"Processing {QName(situation_element.tag).localname}")

        self._imx_file = imx_file
        self._element = situation_element
        self.imx_version = imx_file.imx_version
        self.reference_date = self._parse_date("referenceDate")
        self.perspective_date = self._parse_date("perspectiveDate")
        self.situation_type = self._determine_situation_type()
        self.project_metadata = project_metadata

        self._populate_tree(self._element)
        self._tree.build_exceptions.handle_all()

        # self.dataframes = SingleImxPandasGenerator(self)

    def _parse_date(self, date_type: str) -> datetime | None:
        """Helper method to parse dates from element attributes."""
        return parse_date(self._element.get(date_type, None))

    def _determine_situation_type(self) -> ImxSituationEnum:
        """Determine the situation type from the element tag."""
        tag = self._element.tag
        if isinstance(tag, str):
            return ImxSituationEnum[tag.split("}")[-1]]
        raise NotImplementedError("bytes, bytearray or QName not supported")

    def _populate_tree(self, element: Element):
        self._tree.add_imx_element(element, self._imx_file, self.container_id)

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
        nice_display_ref: bool = True,
    ):
        super().create_geojson_files(directory_path, to_wgs, nice_display_ref)
        dir_path = (
            Path(directory_path) if isinstance(directory_path, str) else directory_path
        )
        if self.project_metadata:
            feature_collection = self.project_metadata.get_geojson(to_wgs)
            file_name = dir_path / "ProjectMetadataAreas.geojson"
            feature_collection.to_geojson_file(file_name)
