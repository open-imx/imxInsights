from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path

from loguru import logger
from lxml import etree
from lxml.etree import _Element as Element

from imxInsights.utils.file import get_http_content_type, zip_folder
from imxInsights.utils.hash import hash_sha256


class FileType(Enum):
    CORE = "core"
    PETAL = "petal"
    MEDIA = "media"


@dataclass
class ManifestFile:
    file: Path
    hash: str
    file_type: FileType
    parent_document_name: str | None = None
    parent_hash_code: str | None = None
    full_path_as_filename: bool = False

    def get_filename(self, input_folder: Path) -> str:
        return (
            str(self.file.relative_to(input_folder))
            if self.full_path_as_filename
            else self.file.name
        )


class ManifestBuilder:
    def __init__(
        self,
        folder_path: Path | str,
        imx_version: str = "12.0.0",
        namespace: str = "http://www.prorail.nl/IMSpoor",
        schema_location: str = "http://www.prorail.nl/IMSpoor IMSpoor-Manifest.xsd",
    ):
        self.folder_path = Path(folder_path)
        self.NAMESPACE = namespace
        self.SCHEMA_LOCATION = schema_location
        self.imx_version = imx_version
        self._file_hashes: dict[Path, str] = {}

    @staticmethod
    def is_old_file(file: Path) -> bool:
        return file.name.endswith("-old.xml")

    def _get_file_hash(self, file: Path) -> str:
        if file not in self._file_hashes:
            self._file_hashes[file] = hash_sha256(file)
        return self._file_hashes[file]

    def _manifest_metadata(self) -> dict:
        return {
            "imxVersion": self.imx_version,
            "coreFileName": "to_fill",
            "nidRbc": "to_fill",
            "nidC": "to_fill",
            "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": self.SCHEMA_LOCATION,
        }

    def _create_manifest_root(self) -> Element:
        nsmap = {
            None: self.NAMESPACE,
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }
        manifest = etree.Element(
            "Manifest", attrib=self._manifest_metadata(), nsmap=nsmap
        )
        manifest.append(etree.Comment(f"Generated on {datetime.now().isoformat()}"))
        manifest.append(etree.Comment("Manifest marked as 'FOR TEST PURPOSES'!"))
        return manifest

    def _parse_xml_root_tag(self, file: Path) -> str | None:
        try:
            return str(etree.parse(file).getroot().tag)
        except etree.XMLSyntaxError:
            logger.error(f"Invalid XML: {file}")
            return None

    def _list_folder_content(self) -> dict:
        core_tag = f"{{{self.NAMESPACE}}}SignalingDesign"
        petal_tags = {
            f"{{{self.NAMESPACE}}}{tag}"
            for tag in [
                "Bgt",
                "Furniture",
                "Legacy",
                "InstallationDesign",
                "ManagementAreas",
                "NetworkConfiguration",
                "Observations",
                "RailwayElectrification",
                "SchemaLayout",
                "TrainControl",
                "Extensions",
            ]
        }
        manifest_tag = f"{{{self.NAMESPACE}}}Manifest"

        all_files: list[ManifestFile] = []
        core_file = None
        core_hash = None

        def crawl(directory: Path):
            nonlocal core_file, core_hash
            for file in directory.iterdir():
                if file.is_dir():
                    crawl(file)
                    continue
                if not file.is_file():
                    continue

                file_hash = self._get_file_hash(file)
                file_type = FileType.MEDIA
                parent_name = parent_hash = None

                if file.suffix.lower() == ".xml":
                    root_tag = self._parse_xml_root_tag(file)
                    if not root_tag or root_tag == manifest_tag:
                        continue

                    if root_tag == core_tag:
                        core_file = file
                        core_hash = file_hash
                        file_type = FileType.CORE
                    elif root_tag in petal_tags:
                        try:
                            tree = etree.parse(file)
                            base_ref = tree.find(
                                f".//{{{self.NAMESPACE}}}BaseReference"
                            )
                            if base_ref is not None:
                                parent_name = base_ref.get("parentDocumentName")
                                parent_hash = base_ref.get("parentHashcode")
                            file_type = FileType.PETAL
                        except Exception as e:
                            logger.error(f"Failed parsing BaseReference in {file}: {e}")

                all_files.append(
                    ManifestFile(
                        file=file,
                        hash=file_hash,
                        file_type=file_type,
                        parent_document_name=parent_name,
                        parent_hash_code=parent_hash,
                        full_path_as_filename=True,
                    )
                )

        crawl(self.folder_path)

        imspoor_files = [
            f
            for f in all_files
            if f.file_type in {FileType.CORE, FileType.PETAL}
            and not self.is_old_file(f.file)
        ]
        media_files = [
            f
            for f in all_files
            if f.file_type == FileType.MEDIA or self.is_old_file(f.file)
        ]

        return {
            "core_file": core_file,
            "core_hash": core_hash,
            "imspoor_files": imspoor_files,
            "media_files": media_files,
        }

    def create_manifest(
        self, file_path: Path | str | None = None, dry_run: bool = False
    ) -> Element | None:
        manifest = self._create_manifest_root()
        data = self._list_folder_content()

        if data["core_file"]:
            manifest.set("coreFileName", data["core_file"].name)

        imspoor_list = etree.SubElement(manifest, "ImSpoorDataList")
        media_list = etree.SubElement(manifest, "MediaList")

        for item in data["imspoor_files"]:
            attributes = {
                "fileName": item.get_filename(self.folder_path),
                "hash": item.hash,
            }
            elem = etree.SubElement(imspoor_list, "ImSpoorData", attrib=attributes)
            if item.parent_document_name != (
                data["core_file"].name if data["core_file"] else None
            ):
                elem.append(etree.Comment("Invalid CoreFile reference."))
            if item.parent_hash_code != data["core_hash"]:
                elem.append(etree.Comment("Invalid ParentHashCode."))

        for item in data["media_files"]:
            attributes = {
                "fileName": item.get_filename(self.folder_path),
                "hash": item.hash,
                "mediaType": get_http_content_type(item.file.name),
            }
            etree.SubElement(media_list, "Media", attrib=attributes)

        if dry_run:
            return manifest

        output_path = (
            Path(file_path) if file_path else self.folder_path / "Manifest.xml"
        )
        with output_path.open("wb") as f:
            f.write(
                etree.tostring(
                    manifest, pretty_print=True, xml_declaration=True, encoding="UTF-8"
                )
            )
        logger.success(f"Manifest created: {output_path}")
        return None

    def to_dict(self) -> dict:
        data = self._list_folder_content()
        return {
            "manifest": self._manifest_metadata()
            | {"coreFileName": data["core_file"].name if data["core_file"] else None},
            "imspoor_files": [asdict(f) for f in data["imspoor_files"]],
            "media_files": [asdict(f) for f in data["media_files"]],
        }

    def to_zip(self, out_path: Path | str) -> None:
        zip_folder(self.folder_path, Path(out_path))

    def validate_manifest(self) -> dict[str, list[str]]:
        manifest_path = self.folder_path / "Manifest.xml"
        results: dict[str, list[str]] = {
            "missing_files": [],
            "extra_files": [],
            "hash_mismatches": [],
            "invalid_core_references": [],
            "invalid_hash_references": [],
            "unexpected_media_type": [],
            "petal_missing_baseref": [],
            "parse_errors": [],
            "validated": [],
        }

        if not manifest_path.exists():
            logger.error("Manifest.xml not found!")
            return results

        NSMAP = {"ims": self.NAMESPACE}
        tree = etree.parse(str(manifest_path))
        root = tree.getroot()

        core_file_name = root.get("coreFileName")
        if not core_file_name:
            logger.error("No coreFileName defined in Manifest.")
            return results

        core_file_path = self.folder_path / core_file_name
        if not core_file_path.exists():
            logger.error(f"Core file '{core_file_name}' not found in folder.")
            return results

        core_hash = self._get_file_hash(core_file_path)
        logger.info(f"Core file: {core_file_name} (hash: {core_hash})")

        files_in_manifest: dict[str, tuple[str, str | None]] = {}

        for elem in root.xpath("//ims:ImSpoorData | //ims:Media", namespaces=NSMAP):
            filename = elem.get("fileName")
            hashcode = elem.get("hash")
            media_type = elem.get("mediaType")
            files_in_manifest[filename] = (hashcode, media_type)

            file_path = self.folder_path / filename
            if not file_path.exists():
                logger.warning(f"File listed in manifest not found: {filename}")
                results["missing_files"].append(filename)
                continue

            actual_hash = self._get_file_hash(file_path)
            has_error = False

            if actual_hash != hashcode:
                logger.warning(
                    f"Hash mismatch for {filename}: expected {hashcode}, got {actual_hash}"
                )
                results["hash_mismatches"].append(filename)
                has_error = True

            tag_name = etree.QName(elem).localname

            if tag_name == "ImSpoorData":
                if media_type is not None:
                    logger.warning(f"Unexpected mediaType in <ImSpoorData>: {filename}")
                    results["unexpected_media_type"].append(filename)
                    has_error = True

                if filename != core_file_name and filename.endswith(".xml"):
                    try:
                        petal_tree = etree.parse(file_path)
                        base_ref = petal_tree.find(
                            ".//ims:BaseReference", namespaces=NSMAP
                        )
                        if base_ref is None:
                            logger.warning(
                                f"Petal file missing BaseReference: {filename}"
                            )
                            results["petal_missing_baseref"].append(filename)
                            has_error = True
                        else:
                            ref_name = base_ref.get("parentDocumentName")
                            ref_hash = base_ref.get("parentHashcode")
                            if ref_name != core_file_name:
                                logger.warning(
                                    f"[{filename}] Invalid CoreFile reference: expected '{core_file_name}', got '{ref_name}'"
                                )
                                results["invalid_core_references"].append(filename)
                                has_error = True
                            if ref_hash != core_hash:
                                logger.warning(
                                    f"[{filename}] Invalid ParentHashCode: expected '{core_hash}', got '{ref_hash}'"
                                )
                                results["invalid_hash_references"].append(filename)
                                has_error = True
                    except Exception as e:
                        logger.error(
                            f"Could not parse {filename} as XML for petal validation: {e}"
                        )
                        results["parse_errors"].append(filename)
                        has_error = True

            if not has_error:
                results["validated"].append(filename)

        # Compare manifest vs. actual files
        all_files = {
            str(f.relative_to(self.folder_path))
            for f in self.folder_path.rglob("*")
            if f.is_file()
        }
        manifest_files = set(files_in_manifest.keys())

        extra_files = all_files - manifest_files - {"Manifest.xml"}
        for f in sorted(extra_files):
            logger.info(f"File not listed in manifest: {f}")
            results["extra_files"].append(f)

        logger.success("Manifest validation complete.")
        return results
