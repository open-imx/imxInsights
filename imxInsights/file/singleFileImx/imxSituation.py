from pathlib import Path

from loguru import logger
from lxml.etree import QName
from lxml.etree import _Element as Element

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSituationEnum import ImxSituationEnum
from imxInsights.repo.imxRepo import ImxRepo


class ImxSituation(ImxRepo):
    """
    Represents a IMX Situation.

    Attributes:
        situation_type: imx situation Type

    """

    def __init__(
        self,
        imx_file_path: Path,
        situation_element: Element,
        imx_file: ImxFile,
    ):
        super().__init__(imx_file_path)
        logger.info(f"processing {QName(situation_element.tag).localname}")
        self.imx_version = imx_file.imx_version
        self.situation_type: ImxSituationEnum = ImxSituationEnum[
            situation_element.tag.split("}")[-1]
        ]
        self._populate_tree(situation_element, imx_file)
        self._tree.build_extensions.handle_all()

    def _populate_tree(self, element: Element, imx_file: ImxFile):
        self._tree.add_imx_element(element, imx_file, self.container_id)
