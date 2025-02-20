import zipfile
from pathlib import Path

import content_types
from loguru import logger


def zip_folder(folder_path: Path, output_path: Path) -> None:
    """
    Compresses the contents of a folder into a ZIP archive.

    Args:
        folder_path: The directory to compress.
        output_path: The destination ZIP file path.

    Raises:
        ValueError: If the provided folder_path is not a valid directory.
    """
    if not folder_path.is_dir():
        raise ValueError(f"Invalid directory: {folder_path}")

    with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file in folder_path.rglob("*"):
            if file.is_file() and file != output_path:
                zip_file.write(file, arcname=file.relative_to(folder_path))

    logger.success(f"Zipped {folder_path} -> {output_path}")


def get_http_content_type(file_name: str) -> str:
    """
    Determines the HTTP content type (MIME type) of a given file.

    Args:
        file_name: The name of the file.

    Returns:
        str: The MIME type of the file, defaulting to 'application/octet-stream'.
    """
    return content_types.get_content_type(file_name) or "application/octet-stream"
