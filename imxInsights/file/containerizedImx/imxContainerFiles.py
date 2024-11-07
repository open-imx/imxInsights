from pathlib import Path
from typing import Any

from imxInsights.file.containerizedImx.imxDesignCoreFile import ImxDesignCoreFile
from imxInsights.file.containerizedImx.imxDesignPetalFile import ImxDesignPetalFile
from imxInsights.file.imxFile import ImxFile


class ImxContainerFiles:
    """
    A data class representing a collection of IMX container files.

    !!! info
        This class holds references to various IMX design files and additional files
        that might be included in an IMX container.

    Attributes:
        manifest (ImxFile | None): The manifest file.
        signaling_design (ImxDesignCoreFile | None): The signaling design file.
        furniture (ImxDesignPetalFile | None): The furniture file.
        train_control (ImxDesignPetalFile | None): The train control file.
        management_areas (ImxDesignPetalFile | None): The management areas file.
        installation_design (ImxDesignPetalFile | None): The installation design file.
        network_configuration (ImxDesignPetalFile | None): The network configuration file.
        schema_layout (ImxDesignPetalFile | None): The schema layout file.
        railway_electrification (ImxDesignPetalFile | None): The railway electrification file.
        bgt (ImxDesignPetalFile | None): The BGT file.
        observations (ImxDesignPetalFile | None): The observations file.
        additional_files (list[Any]): Additional files.

    """

    def __init__(self):
        self.manifest: ImxFile | None = None
        self.signaling_design: ImxDesignCoreFile | None = None
        self.furniture: ImxDesignPetalFile | None = None
        self.train_control: ImxDesignPetalFile | None = None
        self.management_areas: ImxDesignPetalFile | None = None
        self.installation_design: ImxDesignPetalFile | None = None
        self.network_configuration: ImxDesignPetalFile | None = None
        self.schema_layout: ImxDesignPetalFile | None = None
        self.railway_electrification: ImxDesignPetalFile | None = None
        self.bgt: ImxDesignPetalFile | None = None
        self.observations: ImxDesignPetalFile | None = None
        self.additional_files: list[Any] = []

    def __iter__(self):
        if self.manifest is not None:
            yield self.manifest

        if self.signaling_design is not None:
            yield self.signaling_design

        for attr_name in dir(self):
            if not attr_name.startswith("_") and attr_name not in [
                "additional_files",
                "signaling_design",
                "manifest",
                "from_container",
            ]:
                yield getattr(self, attr_name)

    @classmethod
    def from_container(
        cls, container_path: Path, container_id: str
    ) -> "ImxContainerFiles":
        self = cls()

        tag_to_attr = {
            "{http://www.prorail.nl/IMSpoor}SignalingDesign": "signaling_design",
            "{http://www.prorail.nl/IMSpoor}Manifest": "manifest",
            "{http://www.prorail.nl/IMSpoor}Furniture": "furniture",
            "{http://www.prorail.nl/IMSpoor}TrainControl": "train_control",
            "{http://www.prorail.nl/IMSpoor}ManagementAreas": "management_areas",
            "{http://www.prorail.nl/IMSpoor}InstallationDesign": "installation_design",
            "{http://www.prorail.nl/IMSpoor}NetworkConfiguration": "network_configuration",
            "{http://www.prorail.nl/IMSpoor}SchemaLayout": "schema_layout",
            "{http://www.prorail.nl/IMSpoor}RailwayElectrification": "railway_electrification",
            "{http://www.prorail.nl/IMSpoor}Bgt": "bgt",
            "{http://www.prorail.nl/IMSpoor}Observations": "observations",
        }

        for file_path in container_path.glob("*"):
            if file_path.is_file() and file_path.suffix == ".xml":
                imx_file = ImxFile(file_path, container_id)
                if imx_file.imx_version != "12.0.0":
                    raise ValueError(  # noqa: TRY003
                        f"Imx version {imx_file.imx_version} not supported"
                    )

                attr_name = tag_to_attr.get(imx_file.tag)
                if attr_name == "signaling_design":
                    imx_file = ImxDesignCoreFile(file_path, container_id)
                elif attr_name and attr_name != "manifest":
                    imx_file = ImxDesignPetalFile(file_path, container_id)

                if attr_name:
                    if getattr(self, attr_name) is not None:
                        raise ValueError(f"Multiple {attr_name} xml files")  # noqa: TRY003
                    setattr(self, attr_name, imx_file)
            else:
                self.additional_files.append(file_path)

        if not self.signaling_design:
            raise ValueError("No signaling design present in container")  # NOQA TRY003

        return self
