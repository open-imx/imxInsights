import datetime
from pathlib import Path

import dateparser

from imxInsights.file.containerizedImx.imxContainerFile import ImxContainerFile


class ImxDesignCoreFile(ImxContainerFile):
    """
    Represents an IMX design core file, extending ImxContainerFile.

    Args:
        imx_file_path: The path to the IMX file.
        file_id: Optional file ID.
    """

    def __init__(self, imx_file_path: Path, file_id: str | None):
        super().__init__(imx_file_path, file_id)

    @property
    def reference_date(self) -> datetime.datetime | None:
        """
        Gets the reference date attribute from the XML root element.

        Returns:
            The reference date if found, else None.
        """
        if self.root is None:
            return None

        element = self.root.find("[@referenceDate]")

        return (
            dateparser.parse(element.attrib["referenceDate"])
            if element is not None
            else None
        )

    @property
    def perspective_date(self) -> datetime.datetime | None:
        """
        Gets the perspective date attribute from the XML root element.

        Returns:
            The perspective date if found, else None.
        """
        if self.root is None:
            return None

        element = self.root.find("[@perspectiveDate]")
        return (
            dateparser.parse(element.attrib["perspectiveDate"])
            if element is not None
            else None
        )
