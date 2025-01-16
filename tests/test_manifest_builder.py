import zipfile

import pytest
from unittest.mock import patch
from imxInsights.utils.imx.manifestBuilder import ManifestBuilder


@pytest.fixture
def temp_folder(tmp_path):
    """Create a temporary folder with some files for testing."""
    folder = tmp_path / "test_folder"
    folder.mkdir()

    imx_file = folder / "SignalingDesign.xml"
    imx_file.write_text("<root/>")

    media_file = folder / "image.png"
    media_file.write_text("binary data")

    other_file = folder / "other_file.txt"
    other_file.write_text("text data")

    return folder


@patch('imxInsights.utils.hash.hash_sha256')
@patch('imxInsights.utils.file_helpers.get_media_NIME_type')
@patch('imxInsights.utils.file_helpers.zip_folder')
def test_manifest_builder(mock_zip, mock_get_media, mock_hash, temp_folder):
    mock_hash.return_value = "mocked_hash"
    mock_get_media.return_value = "image/png"

    output_zip = temp_folder / "output.zip"
    builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)

    builder.build_manifest()

    manifest = builder.manifest
    assert manifest is not None
    assert manifest.tag == "Manifest"
    assert manifest.attrib["imxVersion"] == "12.0.0"

    im_spoor_data_list = manifest.find("ImSpoorDataList")
    media_list = manifest.find("MediaList")

    im_spoor_data_files = [elem.attrib["fileName"] for elem in im_spoor_data_list.findall("ImSpoorData")]
    media_files = [elem.attrib["fileName"] for elem in media_list.findall("Media")]

    assert "SignalingDesign.xml" in im_spoor_data_files
    assert "SignalingDesign.xml" not in media_files
    assert "image.png" in media_files
    assert "other_file.txt" in media_files

    builder.zip_folder()

    required_files = ["SignalingDesign.xml", "image.png", "other_file.txt", "output.zip"]
    assert all((temp_folder / file).exists() for file in required_files)


def test_save_manifest(temp_folder):
    output_zip = temp_folder / "output.zip"
    builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)
    builder.build_manifest()

    builder.save_manifest()

    manifest_file = temp_folder / "manifest.xml"
    assert manifest_file.exists()

    with open(manifest_file, "rb") as f:
        content = f.read()
        assert b"Manifest" in content


def test_zip_folder(temp_folder):
    output_zip = temp_folder / "output.zip"
    builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)

    builder.zip_folder()

    assert output_zip.exists()

    with zipfile.ZipFile(output_zip, 'r') as zip_file:
        zip_contents = zip_file.namelist()
        assert "SignalingDesign.xml" in zip_contents
        assert "image.png" in zip_contents
