from pathlib import Path

from imxInsights.file.containerizedImx.imxContainerFileReference import (
    ImxContainerFileReference,
)
from imxInsights.file.imxFile import ImxFile


class ImxContainerFile(ImxFile):
    """
    Represents a base class for IMX container files.

    Args:
        imx_file_path: The path to the IMX file.
        file_id: Optional file ID.
    """

    def __init__(self, imx_file_path: Path, file_id: str | None = None):
        super().__init__(imx_file_path, file_id or "")

    @property
    def previous_versions(self) -> list[ImxContainerFileReference]:
        """
        Gets the previous version file references, if present.

        Returns:
            The previous versions.
        """

        if self.root is None:
            return []

        prev_version_node = self.root.find(
            ".//{http://www.prorail.nl/IMSpoor}PreviousVersion"
        )
        return (
            [ImxContainerFileReference.from_element(prev_version_node)]
            if prev_version_node is not None
            else []
        )
