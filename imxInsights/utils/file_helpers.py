import zipfile
from pathlib import Path
import mimetypes
from loguru import logger


def zip_folder(folder_path: Path, output_path: Path):
    """Create a zip file containing the folder's contents, including subdirectories."""
    if not folder_path.is_dir():
        raise ValueError(f"The path {folder_path} is not a valid directory.")

    with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in folder_path.rglob('*'):  # rglob to include subdirectories
            if file_path.is_file():
                zip_file.write(file_path, arcname=file_path.relative_to(folder_path))

    logger.success("Folder {folder_path} has been successfully zipped to {output_path}.")


def get_media_NIME_type(file_name: str) -> str:
    """Return the MIME type of a file."""
    mimetypes.init()
    return mimetypes.guess_type(file_name)[0] or "application/octet-stream"
