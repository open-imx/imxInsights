import hashlib
import json
from pathlib import Path


def hash_sha256(path: Path):
    """
    Calculate the SHA-256 hash sum of a file located at the specified path.

    This function takes a `Path` object representing the path to a file and
    calculates the SHA-256 hash sum of the file's contents. It returns the
    hash sum as a hexadecimal string.

    Args:
        path (Path): The path to the file for which the SHA-256 hash sum
            should be calculated.

    Returns:
        str: A hexadecimal string representing the SHA-256 hash sum of the file.

    Note:
        This function reads the entire contents of the file into memory
        to calculate the hash sum. For large files, this may consume a
        significant amount of memory. Make sure to handle large files
        appropriately when using this function.

    """
    try:
        # Try reading the file and computing the hash
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except PermissionError:
        # Return a default message or error hash if permission is denied
        return "PermissionError: Cannot access file"
    except FileNotFoundError:
        # Handle if the file doesn't exist
        return "FileNotFoundError: File not found"
    except Exception as e:
        # Handle any other exceptions and log or return as needed
        return f"Error: {str(e)}"


def hash_dict_ignor_nested(dictionary: dict) -> str:
    """
    Compute the SHA-1 hash of the dictionary's non-nested values.

    This function takes a dictionary as input and computes the SHA-1 hash of its
    content, excluding nested dictionaries. It extracts non-dictionary values
    from the input dictionary and creates a new dictionary containing only those
    values. Then, it sorts the keys of the new dictionary and computes the SHA-1
    hash of the resulting JSON-encoded string.

    Args:
        dictionary (Dict): The dictionary whose content should be hashed.

    Returns:
        str: A hexadecimal string representing the SHA-1 hash of the non-nested
             values in the dictionary.

    Note:
        This function excludes nested dictionaries when computing the hash,
        focusing only on non-dictionary values. If the input dictionary contains
        nested dictionaries, their content will not be included in the hash.
    """
    new_dict = {}
    for key, value in dictionary.items():
        if not isinstance(value, dict):
            new_dict[key] = value

    hash_object = hashlib.sha1(json.dumps(new_dict, sort_keys=True).encode())
    return hash_object.hexdigest()
