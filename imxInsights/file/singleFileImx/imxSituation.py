from pathlib import Path

from loguru import logger
from lxml.etree import QName
from lxml.etree import _Element as Element
from pydantic.schema import datetime

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSingleFileMetadata import SingleImxMetadata
from imxInsights.file.singleFileImx.imxSituationEnum import ImxSituationEnum
from imxInsights.repo.imxRepo import ImxRepo
from imxInsights.report.singleImxPandasGenerator import SingleImxPandasGenerator
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

        # Initialize attributes with helper functions to clean up constructor
        self._imx_file = imx_file
        self._element = situation_element
        self.imx_version = imx_file.imx_version
        self.reference_date = self._parse_date("referenceDate")
        self.perspective_date = self._parse_date("perspectiveDate")
        self.situation_type = self._determine_situation_type()

        self._populate_tree(self._element)
        self._tree.build_exceptions.handle_all()

        self.pandas_generator = SingleImxPandasGenerator(
            container_id=self.container_id,
            project_metadata=project_metadata if project_metadata else None,
            imx_file=imx_file,
            input_file_path=imx_file_path,
            build_exceptions=self._tree.build_exceptions,
            situation=self.situation_type,
            reference_date=self.reference_date if self.reference_date else None,
            perspective_date=self.perspective_date if self.perspective_date else None,
        )

    def _parse_date(self, date_type: str) -> datetime | None:
        """Helper method to parse dates from element attributes."""
        return parse_date(self._element.get(date_type, None))

    def _determine_situation_type(self) -> ImxSituationEnum:
        """Determine the situation type from the element tag."""
        return ImxSituationEnum[self._element.tag.split("}")[-1]]

    def _populate_tree(self, element: Element):
        self._tree.add_imx_element(element, self._imx_file, self.container_id)
