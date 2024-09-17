from pathlib import Path

from loguru import logger

from imxInsights.file.containerizedImx.imxContainerFiles import ImxContainerFiles
from imxInsights.file.containerizedImx.imxContainerMetadata import ImxContainerMetadata
from imxInsights.repo.imxRepo import ImxRepo


class ImxContainer(ImxRepo):
    """
    Represents an IMX container.

    Args:
        imx_file_path: Path to the IMX container.

    Attributes:
        files: The IMX files inside the container

    """

    def __init__(self, imx_file_path: Path | str):
        logger.info(f"processing {Path(imx_file_path).name}")
        super().__init__(imx_file_path)

        if not self.path.is_dir():
            raise ValueError("container is not a valid directory, zip or path string")  # noqa: TRY003

        self.files: ImxContainerFiles = ImxContainerFiles.from_container(
            container_path=self.path, container_id=self.container_id
        )
        self.imx_version = (
            self.files.signaling_design.imx_version
            if self.files.signaling_design
            else None
        )
        self._populate_project_metadata()
        self._populate_tree()
        self._tree.build_extensions.handle_all()
        logger.success(f"finished processing {Path(imx_file_path).name}")

    def _populate_project_metadata(self):
        if self.files.signaling_design is not None:
            self.project_metadata = ImxContainerMetadata.from_element(
                self.files.signaling_design.root
            )

    def _populate_tree(self):
        if self.files.signaling_design is not None:
            self._tree.add_imx_file(self.files.signaling_design, self.container_id)

            for petal in [
                "furniture",
                "train_control",
                "management_areas",
                "installation_design",
                "network_configuration",
                "schema_layout",
                "railway_electrification",
                "bgt",
                "observations",
            ]:
                imx_file = getattr(self.files, petal)
                if imx_file is not None:
                    self._tree.add_imx_file(imx_file, self.container_id)
