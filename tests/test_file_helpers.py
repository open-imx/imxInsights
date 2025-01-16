import pytest
from pathlib import Path
import zipfile

from imxInsights.utils.file_helpers import zip_folder, get_media_NIME_type


@pytest.fixture
def temp_folder(tmp_path):
    """Create a temporary folder with some files."""
    folder = tmp_path / "test_folder"
    folder.mkdir()

    file_1 = folder / "file1.txt"
    file_1.write_text("This is a test file.")

    subfolder = folder / "subfolder"
    subfolder.mkdir()
    file_2 = subfolder / "file2.txt"
    file_2.write_text("This is another test file.")

    return folder


def test_zip_folder_valid(temp_folder, tmp_path):
    output_zip = tmp_path / "output.zip"
    zip_folder(temp_folder, output_zip)
    assert output_zip.exists()
    with zipfile.ZipFile(output_zip, 'r') as zip_file:
        zip_contents = zip_file.namelist()
        assert "file1.txt" in zip_contents
        assert "subfolder/file2.txt" in zip_contents


def test_zip_folder_invalid_directory(tmp_path):
    invalid_folder = tmp_path / "invalid_folder"
    with pytest.raises(ValueError):
        zip_folder(invalid_folder, tmp_path / "output.zip")


def test_get_media_NIME_type():
    # Known file types
    assert get_media_NIME_type("file1.txt") == "text/plain"
    assert get_media_NIME_type("image.png") == "image/png"
    assert get_media_NIME_type("audio.mp3") == "audio/mpeg"

    # Unknown file type
    assert get_media_NIME_type("unknownfile.xyz") == "application/octet-stream"
