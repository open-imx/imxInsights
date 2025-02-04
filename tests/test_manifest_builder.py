# import zipfile
# import tempfile
# import os
# from pathlib import Path
#
# import pytest
# from unittest.mock import patch
# from imxInsights.utils.imx.manifestBuilder import ManifestBuilder
#
#
# @pytest.fixture
# def temp_folder():
#     """Create a temporary folder with some files for testing."""
#     with tempfile.TemporaryDirectory() as temp_dir:
#         folder = Path(temp_dir) / "test_folder"
#         folder.mkdir()  # Create the directory
#
#         # Create files inside the temporary folder
#         imx_file = folder / "SignalingDesign.xml"
#         with open(imx_file, "w") as f:
#             f.write("<root/>")
#
#         media_file = folder / "image.png"
#         with open(media_file, "w") as f:
#             f.write("binary data")
#
#         other_file = folder / "other_file.txt"
#         with open(other_file, "w") as f:
#             f.write("text data")
#
#         # Log folder creation for debugging purposes
#         print(f"Temp folder created at: {folder}")
#         print(f"Temp folder contents: {os.listdir(folder)}")
#
#         yield folder  # This will be returned as the fixture result
#
#
# @patch('imxInsights.utils.hash.hash_sha256')
# @patch('imxInsights.utils.file_helpers.get_media_NIME_type')
# @patch('imxInsights.utils.file_helpers.zip_folder')
# def test_manifest_builder(mock_zip, mock_get_media, mock_hash, temp_folder):
#     mock_hash.return_value = "mocked_hash"
#     mock_get_media.return_value = "image/png"
#
#     # Ensure we pass Path, not string
#     output_zip = temp_folder / "output.zip"
#     builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)
#
#     builder.build_manifest()
#
#     manifest = builder.manifest
#     assert manifest is not None
#     assert manifest.tag == "Manifest"
#     assert manifest.attrib["imxVersion"] == "12.0.0"
#
#     im_spoor_data_list = manifest.find("ImSpoorDataList")
#     media_list = manifest.find("MediaList")
#
#     im_spoor_data_files = [elem.attrib["fileName"] for elem in im_spoor_data_list.findall("ImSpoorData")]
#     media_files = [elem.attrib["fileName"] for elem in media_list.findall("Media")]
#
#     assert "SignalingDesign.xml" in im_spoor_data_files
#     assert "SignalingDesign.xml" not in media_files
#     assert "image.png" in media_files
#     assert "other_file.txt" in media_files
#
#     builder.zip_folder()
#
#     required_files = ["SignalingDesign.xml", "image.png", "other_file.txt", "output.zip"]
#     assert all((temp_folder / file).exists() for file in required_files)
#
# def test_save_manifest(temp_folder):
#     output_zip = os.path.join(temp_folder, "output.zip")
#     builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)
#     builder.build_manifest()
#
#     builder.save_manifest()
#
#     manifest_file = os.path.join(temp_folder, "manifest.xml")
#     assert os.path.exists(manifest_file)
#
#     with open(manifest_file, "rb") as f:
#         content = f.read()
#         assert b"Manifest" in content
#
#
# def test_zip_folder(temp_folder):
#     output_zip = os.path.join(temp_folder, "output.zip")
#     builder = ManifestBuilder(folder_path=temp_folder, output_zip=output_zip)
#
#     builder.zip_folder()
#
#     assert os.path.exists(output_zip)
#
#     with zipfile.ZipFile(output_zip, 'r') as zip_file:
#         zip_contents = zip_file.namelist()
#         assert "SignalingDesign.xml" in zip_contents
#         assert "image.png" in zip_contents
