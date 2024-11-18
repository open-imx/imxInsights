from pathlib import Path

from loguru import logger

from imxInsights.file.containerizedImx.imxContainerFiles import ImxContainerFiles
from imxInsights.file.containerizedImx.imxContainerMetadata import ImxContainerMetadata
from imxInsights.repo.imxRepo import ImxRepo

# from imxInsights.report.containerImxPandasGenerator import ContainerImxPandasGenerator


class ImxContainer(ImxRepo):
    """
    Represents an IMX container.

    Args:
        imx_file_path: Path to the IMX container.

    Attributes:
        files: The IMX files inside the container.
        imx_version: Version of the IMX files.
        project_metadata: Metadata associated with the project.
        dataframes: Pandas dataframes generated from the IMX container.
    """

    def __init__(self, imx_file_path: Path | str):
        self._input_file_path = self._initialize_file_path(imx_file_path)
        super().__init__(self._input_file_path)

        self._validate_container_path()
        self.files = self._load_imx_files()
        self.imx_version = self._get_imx_version()
        self.project_metadata = self._populate_project_metadata()
        self._populate_tree()

        logger.success(f"Finished processing {self._input_file_path.name}")
        # self.dataframes = ContainerImxPandasGenerator(self)

    @staticmethod
    def _initialize_file_path(imx_file_path: Path | str) -> Path:
        """Initialize and return a Path object from the input file path."""
        logger.info(f"Processing {Path(imx_file_path).name}")
        return Path(imx_file_path) if isinstance(imx_file_path, str) else imx_file_path

    def _validate_container_path(self):
        """Validate that the given path is a valid directory or file."""
        if not self.path.is_dir():
            raise ValueError("Container is not a valid directory, zip, or path string")  # NOQA TRY003

    def _load_imx_files(self) -> ImxContainerFiles:
        """Load IMX files from the container path."""
        return ImxContainerFiles.from_container(
            container_path=self.path, container_id=self.container_id
        )

    def _get_imx_version(self) -> str | None:
        """Retrieve the IMX version from the signaling design."""
        return (
            self.files.signaling_design.imx_version
            if self.files.signaling_design
            else None
        )

    def _populate_project_metadata(self) -> ImxContainerMetadata | None:
        """Populate and return project metadata."""
        if self.files.signaling_design is not None:
            return ImxContainerMetadata.from_element(self.files.signaling_design.root)
        return None

    def _populate_tree(self):
        """Populate the tree structure with IMX files."""
        if self.files.signaling_design is not None:
            self._tree.add_imx_file(self.files.signaling_design, self.container_id)
            self._add_additional_imx_files()

    def _add_additional_imx_files(self):
        """Add additional IMX files to the tree structure."""
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
