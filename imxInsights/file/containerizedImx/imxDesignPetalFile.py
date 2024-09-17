from pathlib import Path

from imxInsights.file.containerizedImx.imxContainerFile import ImxContainerFile
from imxInsights.file.containerizedImx.imxContainerFileReference import (
    ImxContainerFileReference,
)


class ImxDesignPetalFile(ImxContainerFile):
    """
    Represents an IMX design petal file, should extend a ImxDesignCoreFile repo.

    Args:
        imx_file_path: The path to the IMX file.
        file_id: Optional file ID.

    """

    def __init__(self, imx_file_path: Path, file_id: str | None):
        super().__init__(imx_file_path, file_id)

    @property
    def base_reference(self) -> ImxContainerFileReference | None:
        """
        Gets the base reference file reference, if available.

        Returns:
            The BaseReference of the petal file.
        """
        if self.root is None:
            return None

        base_ref_node = self.root.find(
            ".//{http://www.prorail.nl/IMSpoor}BaseReference"
        )
        if base_ref_node is not None:
            return ImxContainerFileReference.from_element(base_ref_node)
        return None
