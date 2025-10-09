import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

from imxInsights.file.containerizedImx.imxDesignCoreFile import ImxDesignCoreFile
from imxInsights.file.containerizedImx.imxDesignPetalFile import ImxDesignPetalFile
from imxInsights.file.imxFile import ImxFile


class ImxContainerFiles:
    """
    A data class representing a collection of IMX container files.

    Attributes:
        manifest (ImxFile | None)
        signaling_design (ImxDesignCoreFile | None)
        furniture (ImxDesignPetalFile | None)
        train_control (ImxDesignPetalFile | None)
        management_areas (ImxDesignPetalFile | None)
        installation_design (ImxDesignPetalFile | None)
        network_configuration (ImxDesignPetalFile | None)
        schema_layout (ImxDesignPetalFile | None)
        railway_electrification (ImxDesignPetalFile | None)
        bgt (ImxDesignPetalFile | None)
        observations (ImxDesignPetalFile | None)
        kilometer_values (ImxDesignPetalFile | None)
        reference_systems (ImxDesignPetalFile | None)
        additional_files (list[Any])
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
        self.kilometer_values: ImxDesignPetalFile | None = None
        self.reference_systems: ImxDesignPetalFile | None = None
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
                "_find_manifest_path",
                "_normalize_rel",
                "_ensure_supported_version",
            ]:
                yield getattr(self, attr_name)

    # ----------------------- helpers -----------------------

    @staticmethod
    def _find_manifest_path(container_path: Path) -> Path:
        """Return path to Manifest.xml in root (case-insensitive)."""
        for name in ("Manifest.xml", "manifest.xml"):
            p = container_path / name
            if p.exists() and p.is_file():
                return p
        raise FileNotFoundError("Manifest.xml not found in container root")

    @staticmethod
    def _normalize_rel(path_str: str) -> Path:
        """Normalize a manifest relative path (handles backslashes)."""
        return Path(path_str.replace("\\", "/"))

    @staticmethod
    def _ensure_supported_version(imx_file: ImxFile) -> None:
        if imx_file.imx_version not in {"12.0.0", "14.0.0", "15.0.0"}:
            raise ValueError(f"Imx version {imx_file.imx_version} not supported")  # noqa: TRY003

    # ----------------------- main loader -----------------------

    @classmethod
    def from_container(
        cls, container_path: Path, container_id: str
    ) -> "ImxContainerFiles":
        self = cls()

        # 1) Find + load the Manifest from root
        manifest_path = cls._find_manifest_path(container_path)
        self.manifest = ImxFile(manifest_path, container_id)

        # 2) Parse Manifest for ImSpoorData entries
        ns = {"imx": "http://www.prorail.nl/IMSpoor"}
        try:
            tree = ET.parse(manifest_path)
        except ET.ParseError as e:
            raise ValueError(f"Failed to parse Manifest.xml: {e}")  # noqa: TRY003

        root = tree.getroot()
        imspoor_list = root.find("imx:ImSpoorDataList", ns)
        if imspoor_list is None:
            raise ValueError("Manifest missing <ImSpoorDataList>")  # noqa: TRY003

        items: list[tuple[str, str]] = []
        for el in imspoor_list.findall("imx:ImSpoorData", ns):
            file_name = el.get("fileName")
            imx_type = el.get("ImxType")
            if not file_name or not imx_type:
                raise ValueError("ImSpoorData missing fileName or ImxType")  # noqa: TRY003
            items.append((file_name, imx_type))

        if not items:
            raise ValueError("Manifest contains no ImSpoorData entries")  # noqa: TRY003

        # 3) Map ImxType to attributes on this class (incl. KilometerValues, ReferenceSystems)
        imxtype_to_attr: dict[str, str] = {
            "SignalingDesign": "signaling_design",
            "Manifest": "manifest",
            "Furniture": "furniture",
            "TrainControl": "train_control",
            "ManagementAreas": "management_areas",
            "InstallationDesign": "installation_design",
            "NetworkConfiguration": "network_configuration",
            "SchemaLayout": "schema_layout",
            "RailwayElectrification": "railway_electrification",
            "Bgt": "bgt",
            "Observations": "observations",
            "KilometerValues": "kilometer_values",
            "ReferenceSystems": "reference_systems",
        }
        petal_types = {
            t for t in imxtype_to_attr if t not in {"SignalingDesign", "Manifest"}
        }

        # 4) Load each listed file from the root (respecting subfolders)
        loaded_paths = {manifest_path.resolve()}

        for file_name, imx_type in items:
            rel = cls._normalize_rel(file_name)
            abs_path = (container_path / rel).resolve()

            # ensure path stays inside container root
            try:
                abs_path.relative_to(container_path.resolve())
            except ValueError:
                raise ValueError(f"Manifest file points outside container: {rel}")  # noqa: TRY003

            if not abs_path.exists() or not abs_path.is_file():
                raise FileNotFoundError(f"File from Manifest not found: {rel}")  # noqa: TRY003

            attr_name = imxtype_to_attr.get(imx_type)

            # choose the right class
            if imx_type == "SignalingDesign":
                imx_obj: ImxFile = ImxDesignCoreFile(abs_path, container_id)
            elif imx_type in petal_types:
                imx_obj = ImxDesignPetalFile(abs_path, container_id)
            elif imx_type == "Manifest":
                imx_obj = ImxFile(abs_path, container_id)
            else:
                # Unknown type: generic file + stash as additional
                imx_obj = ImxFile(abs_path, container_id)
                self.additional_files.append(abs_path)
                loaded_paths.add(abs_path)
                cls._ensure_supported_version(imx_obj)
                continue

            # version check
            cls._ensure_supported_version(imx_obj)

            if attr_name:
                if getattr(self, attr_name) is not None:
                    raise ValueError(f"Multiple {attr_name} files in container")  # noqa: TRY003
                setattr(self, attr_name, imx_obj)
            else:
                self.additional_files.append(abs_path)

            loaded_paths.add(abs_path)

        # 5) Record other root entries as additional_files (not listed in manifest)
        for entry in container_path.glob("*"):
            try:
                if entry.resolve() not in loaded_paths:
                    self.additional_files.append(entry)
            except FileNotFoundError:
                continue

        # 6) Ensure core presence
        if not self.signaling_design:
            raise ValueError("No signaling design present in container")  # NOQA TRY003

        return self
