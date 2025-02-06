import mimetypes
import zipfile
from pathlib import Path

from loguru import logger
from lxml import etree
from lxml.etree import _Element as Element

from imxInsights.utils.hash import hash_sha256

# should not be included in this library, implicit create mutate feature.


def zip_folder(folder_path: Path, output_path: Path):  # pragma: no cover
    """Create a zip file containing the folder's contents, including subdirectories."""
    if not folder_path.is_dir():
        raise ValueError(f"The path {folder_path} is not a valid directory.")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in folder_path.rglob("*"):  # rglob to include subdirectories
            if file_path.is_file():
                zip_file.write(file_path, arcname=file_path.relative_to(folder_path))

    logger.success(
        "Folder {folder_path} has been successfully zipped to {output_path}."
    )


def get_media_NIME_type(file_name: str) -> str:  # pragma: no cover
    """Return the MIME type of a file."""
    mimetypes.init()
    return mimetypes.guess_type(file_name)[0] or "application/octet-stream"


class ManifestBuilder:  # pragma: no cover
    def __init__(self, folder_path: Path, output_zip: Path):
        self.folder_path = folder_path
        self.output_zip_path = output_zip
        self.im_spoor_files = {"SignalingDesign.xml"}
        self.manifest: Element | None = None

    @staticmethod
    def _create_manifest_xml_imx_12() -> Element:
        nsmap = {
            None: "http://www.prorail.nl/IMSpoor",
            "xsi": "http://www.w3.org/2001/XMLSchema-instance",
            "gml": "http://www.opengis.net/gml",
        }
        manifest = etree.Element(
            "Manifest",
            attrib={
                "imxVersion": "12.0.0",
                "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": "http://www.prorail.nl/IMSpoor IMSpoor-Manifest.xsd",
                "coreFileName": "SignalingDesign.xml",
                "nidRbc": "to_fill",
                "nidC": "to_fill",
            },
            nsmap=nsmap,
        )
        manifest.append(
            etree.Comment(
                "This IMX 12 manifest is created (and zipped as a container) using imxInsights, see open-imx.nl for more information."
            )
        )
        manifest.append(
            etree.Comment(
                'Manifest and zip container currently marked as "INTENDED FOR TEST PURPOSES"!'
            )
        )
        return manifest

    def _add_file_to_list(
        self, file_name: str, parent_element: Element, file_type: str
    ):
        file_path = self.folder_path / file_name
        if file_path.is_file():
            file_hash = hash_sha256(file_path)
            if file_type == "imspoor":
                etree.SubElement(
                    parent_element,
                    "ImSpoorData",
                    attrib={"fileName": file_name, "hash": file_hash},
                )
            elif file_type == "media":
                media_type = get_media_NIME_type(file_name)
                etree.SubElement(
                    parent_element,
                    "Media",
                    attrib={
                        "fileName": file_name,
                        "mediaType": media_type,
                        "hash": file_hash,
                    },
                )

    def _add_im_spoor_data_imx_12(self, manifest: Element):
        # todo: check core file hash, and if not based on same hash add comment to manifest
        im_spoor_data_list = etree.SubElement(manifest, "ImSpoorDataList")
        for file in self.folder_path.iterdir():
            if file.name in self.im_spoor_files:
                self._add_file_to_list(file.name, im_spoor_data_list, "imspoor")

    def _add_media_data_imx_12(self, manifest: Element):
        media_list = etree.SubElement(manifest, "MediaList")
        for file in self.folder_path.iterdir():
            if file.name not in self.im_spoor_files and file.name != "Manifest.xml":
                self._add_file_to_list(file.name, media_list, "media")

    def _build_manifest_imx12(self) -> Element:
        manifest = self._create_manifest_xml_imx_12()
        self._add_im_spoor_data_imx_12(manifest)
        self._add_media_data_imx_12(manifest)
        return manifest

    def build_manifest(self):
        """Build the (IMX v12) manifest element from folder contents."""
        self.manifest = self._build_manifest_imx12()

    def save_manifest(self):
        """Save the generated manifest to a file."""
        if self.manifest is None:
            raise ValueError(
                "Manifest has not been built yet. Call build_manifest() first."
            )

        manifest_file = self.folder_path / "Manifest.xml"
        with open(manifest_file, "wb") as f:
            # noinspection PyDeprecation
            f.write(
                etree.tostring(
                    self.manifest,
                    pretty_print=True,
                    xml_declaration=True,
                    encoding="UTF-8",
                )
            )

    def zip_folder(self):
        """Create a zip file containing the folder's contents."""
        zip_folder(self.folder_path, self.output_zip_path)


if __name__ == "__main__":  # pragma: no cover
    folder = Path(input("input folder"))
    output = Path(input("output zip file"))
    builder = ManifestBuilder(
        folder,
        output,
    )
    builder.build_manifest()
    builder.save_manifest()
    builder.zip_folder()
