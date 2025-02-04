import uuid
from pathlib import Path

from lxml.etree import _Element as Element
from lxml.etree import _ElementTree as ElementTree

from imxInsights.file.xmlFile import XmlFile


class ImxFile:
    """
    Represents an IMX file.

    Args:
        imx_file_path: The path to the IMX file.
        file_id: The UUID4 of the container.

    Attributes:
        imx_version: The IMX version.
        file_id: The ID of the container.
        file_hash: The hash of the file.
        path: Path object of the imx file.
        absolute_path: Gets the absolute path of the file.
        tag: The tag of the XML root element.
    """

    def __init__(self, imx_file_path: Path, file_id: str = str(uuid.uuid4())):
        # todo: should handle strings aswel, make sure file exist else raise error.
        # todo: check if valid UUID if string is given else raise error.
        self.input_path: str | Path = imx_file_path
        self._xml_file: XmlFile = XmlFile(self.input_path)
        self.container_id: str = file_id

        if self._xml_file.root is None:
            raise ValueError("Root of the XML file is None")  # noqa: TRY003

        imx_version_element: Element | None = self._xml_file.root.find("[@imxVersion]")

        if (
            imx_version_element is None
            or "imxVersion" not in imx_version_element.attrib
        ):
            raise ValueError("imxVersion attribute not found")  # noqa: TRY003

        self.imx_version: str = imx_version_element.attrib["imxVersion"]

    @property
    def file_hash(self) -> str:
        return self._xml_file.file_hash if self._xml_file.file_hash else ""

    @property
    def path(self) -> Path:
        return self._xml_file.path

    @property
    def absolute_path(self) -> str:
        return str(self._xml_file.path.absolute())

    @property
    def tag(self) -> str:
        return self._xml_file.tag if self._xml_file.tag else ""

    @property
    def root(self) -> ElementTree | None:
        return self._xml_file.root
