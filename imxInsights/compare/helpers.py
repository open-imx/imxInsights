import re
from typing import Any

from imxInsights.utils.shapely_gml import GmlShapleyFactory


def transform_dict(d: dict[str, Any]) -> dict[str, Any]:
    """
    Transforms a dictionary by grouping list items based on their indexed keys.

    This function processes a dictionary where keys may contain indexed parts
    indicating list items (e.g., 'key.0.subkey'). It transforms the dictionary
    by consolidating these list items into structured lists under their base paths.

    Args:
        d : A dictionary with keys that may represent nested structures with indexed list items.

    Returns:
        A transformed dictionary where indexed list items are grouped under their respective base paths.
    """
    result: dict[str, Any] = {}
    temp_dict: dict[str, list[dict[str, Any]]] = {}

    for key, value in d.items():
        parts = key.split(".")

        # Check if the second last part is a digit (indicating list index)
        if len(parts) > 1 and parts[-2].isdigit():
            list_index = int(parts[-2])
            # Get the path up to the list
            base_path = ".".join(parts[:-2])

            if base_path not in temp_dict:
                temp_dict[base_path] = []

            # Ensure the list is long enough
            while len(temp_dict[base_path]) <= list_index:
                temp_dict[base_path].append({})

            # Remove the list index from the key for the list item
            item_key = ".".join(parts[-1:])  # Keep the key name without the index
            temp_dict[base_path][list_index][item_key] = value
        else:
            result[key] = value

    # Merge list items into the result dictionary
    for path, items in temp_dict.items():
        if items:
            result[path] = items

    return result


def remove_empty_dicts(data: dict | list | Any) -> dict | Any:
    """
    Recursively removes empty dictionaries from a nested data structure.

    This function traverses through a nested dictionary or list and removes
    any dictionary where all values are `None`. It handles arbitrarily
    deep nesting of dictionaries and lists.

    Args:
        data: The input data structure, which can be a dictionary, list, or any other type.

    Returns:
        The cleaned data structure with empty dictionaries removed.
    """
    if isinstance(data, dict):
        # Recursively check each key in the dictionary
        for key, value in list(data.items()):
            data[key] = remove_empty_dicts(value)

    elif isinstance(data, list):
        # Iterate through the list and clean each item
        new_list = []
        for item in data:
            cleaned_item = remove_empty_dicts(item)
            # Check if the cleaned item is not an empty dictionary
            if not (
                isinstance(cleaned_item, dict)
                and all(v is None for v in cleaned_item.values())
            ):
                new_list.append(cleaned_item)
        return new_list

    return data


def parse_dict_to_value_objects(input_dict: dict[str, Any]) -> dict[str, Any]:
    """
    Parses GML elements in the input dictionary to Shapely objects or converts
    string representations of numbers to their respective types.

    This function processes each key-value pair in the input dictionary,
    converting string representations of coordinates into Shapely geometry
    objects and strings containing numeric values to their respective numeric types.

    Args:
        input_dict: A dictionary where keys are strings and values can be GML elements,
                    numeric strings, or any other types.

    Returns:
        A dictionary with GML elements converted to Shapely objects and numeric strings
        converted to their respective types (int or float).
    """
    for key, value in input_dict.items():
        if isinstance(value, str):
            if "." in value:
                try:
                    input_dict[key] = float(value)
                    continue
                except ValueError:
                    pass
            else:
                try:
                    input_dict[key] = int(value)
                    continue
                except ValueError:
                    pass

        if "Point.coordinates" in key and isinstance(value, str):
            shapley_point = GmlShapleyFactory.gml_point_to_shapely(value)
            input_dict[key] = shapley_point

        elif "LineString.coordinates" in key and isinstance(value, str):
            shapley_line = GmlShapleyFactory.gml_linestring_to_shapely(value)
            input_dict[key] = shapley_line

        elif "Polygon.coordinates" in key and isinstance(value, str):
            shapley_polygon = GmlShapleyFactory.gml_polygon_to_shapely(value)
            input_dict[key] = shapley_polygon

    return input_dict


def convert_deepdiff_path(deepdiff_path: str) -> str:
    """
    Converts a DeepDiff path to a dot-separated path format using regular expressions.

    This function takes a DeepDiff path and transforms it into a dot-separated format
    by removing unnecessary characters and adjusting the path representation for easier use.

    Args:
        deepdiff_path: A string representing the path from DeepDiff, typically formatted
                       with brackets and quotes.

    Returns:
        A string representing the converted path in a dot-separated format.
    """
    # Remove "root" at the beginning if it exists
    if deepdiff_path.startswith("root"):
        deepdiff_path = deepdiff_path[4:]  # Remove "root"

    # Replace the pattern ['key'] with .key
    deepdiff_path = re.sub(r"\['([^']+)'\]", r".\1", deepdiff_path)

    # Replace patterns like [0] with .0
    deepdiff_path = re.sub(r"\[(\d+)\]", r".\1", deepdiff_path)

    # Remove any leading '.' that might have resulted from replacements
    deepdiff_path = deepdiff_path.lstrip(".")

    return deepdiff_path


def merge_dict_keep_first_key(d: dict) -> dict:
    """
    Merges a dictionary by keeping the first occurrence of each key (case-insensitive).

    This function processes a dictionary and merges keys while preserving the first key's
    original case. If duplicate keys (case-insensitive) are found, their values are merged
    based on their types:
    - Lists are concatenated.
    - Dictionaries are merged recursively.
    - Other values are replaced by the most recent occurrence.

    Args:
        d: The dictionary to be merged, where keys may have different cases.

    Returns:
        A new dictionary with merged keys and values, maintaining the first key's original case.
    """
    merged_dict: dict[str, Any] = {}
    original_keys: dict[str, Any] = {}

    for key, value in d.items():
        lower_key = key.lower()

        if lower_key in original_keys:
            original_key = original_keys[lower_key]
            if isinstance(merged_dict[original_key], list) and isinstance(value, list):
                merged_dict[original_key].extend(value)
            elif isinstance(merged_dict[original_key], dict) and isinstance(
                value, dict
            ):
                merged_dict[original_key] = merge_dict_keep_first_key(
                    {**merged_dict[original_key], **value}
                )
            else:
                merged_dict[original_key] = value
        else:
            merged_dict[key] = value
            original_keys[lower_key] = key  # Track the first occurrence of the key

    return merged_dict
