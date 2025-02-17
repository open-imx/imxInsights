import re
from collections import defaultdict
from typing import Any

from imxInsights.utils.hash import hash_dict_ignor_nested


def flatten_dict(
    data_dict: dict[str, dict[Any, Any] | str | list[Any]],
    skip_key: str | None = "@puic",
    prefix="",
    sep=".",
) -> dict[str, str]:
    def _custom_sorting(key_, remaining_: list[dict]):
        mapping = {
            "RailConnectionInfo": "@railConnectionRef",
            "Announcement": "@installationRef",
        }

        if key_ in mapping.keys():
            # Use safe retrieval with get() and provide a default value for missing keys or incompatible types.
            return sorted(
                remaining_,
                key=lambda x: x.get(mapping[key_], "")
                if isinstance(x.get(mapping[key_]), int | float | str)
                else "",
            )
        else:
            return sorted(remaining_, key=hash_dict_ignor_nested)

    result: dict[str, str] = {}

    # Skip root node if this is a recursive call and key is found
    if prefix and skip_key in data_dict:
        return result

    for key, value in data_dict.items():
        if not isinstance(value, list) and not isinstance(value, dict):
            result[f"{prefix}{key}"] = value
            continue

        new_prefix = f"{prefix}{key}{sep}"

        if (
            isinstance(value, list)
            and len(value) > 0
            and not isinstance(value[0], dict)
        ):
            # add index and add to current.
            for i, child in enumerate(value):
                result[f"{new_prefix}{i}"] = child
            continue

        # Multiple children -> list of dicts. Convert single dict to list with dict.
        if isinstance(value, dict):
            value = [value]

        if len(value) != 0:
            assert len(value) > 0 and isinstance(value[0], dict)

        # Filter children with skip_key.
        remaining = list[dict]() if skip_key is not None else value
        if skip_key is not None:
            for child in value:
                if skip_key in child:
                    continue
                remaining.append(child)

        # Add index for each child if >1 and recurse, order can be changed in xml, so sort before indexing..
        if len(remaining) > 1:
            # sorting is done on a specified key.
            # if no key is present make hash of attributes, if no attributes hash first node attributes...
            remaining = _custom_sorting(key, remaining)

        for i, child in enumerate(remaining):
            child_prefix = f"{new_prefix}{i}{sep}" if len(remaining) > 1 else new_prefix
            flattened = flatten_dict(
                child, skip_key=skip_key, prefix=child_prefix, sep=sep
            )
            result = result | flattened

    return result


def parse_to_nested_dict(input_dict: dict[str, Any]) -> dict[str | int, Any]:
    result: dict[str | int, Any] = {}

    for key, value in input_dict.items():
        parts = key.split(".")
        d = result

        # Traverse through parts except the last one
        for part in parts[:-1]:
            if part.isdigit():
                part = str(int(part))
            if isinstance(d, list):
                # If current dictionary is a list, append a new dictionary for the current part
                d.append({})
                d = d[-1]
            if part not in d:
                # Ensure the current part is a dictionary
                d[part] = {}
            d = d[part]

        # Handle the last part of the key
        last_part = parts[-1]
        if last_part.isdigit():
            last_part = str(int(last_part))

        if isinstance(d, list):
            d.append(value)
        else:
            d[last_part] = value

    return result


def sort_dict_by_sourceline(data):
    keys = [k for k in data]  # if not k.endswith(':sourceline')]
    sorted_keys = sorted(keys, key=lambda k: int(data.get(f"{k}:sourceline", 1e9)))
    sorted_data = {k: data[k] for k in sorted_keys}
    return sorted_data


def remove_sourceline_from_dict(dict_whit_sourcelines: dict[str, Any]):
    return {
        k: v for k, v in dict_whit_sourcelines.items() if not k.endswith(":sourceline")
    }


def reindex_dict(data: dict[str, str]) -> dict[str, str]:
    # Initialize an empty dictionary to store the new data with reindexed keys
    new_data: dict[str, Any] = {}

    # index_map keeps track of the mapping from parent key (path) to a dictionary of
    # original indices and their corresponding new indices for each parent
    index_map: defaultdict[str, dict[str, int]] = defaultdict(dict)

    # counter_map tracks how many items we've seen under each parent to assign new indices
    counter_map: defaultdict[str, int] = defaultdict(int)

    # Iterate through each key-value pair in the input dictionary
    for key, value in data.items():
        # Split the key by dots to get individual segments (path parts)
        parts: list[str] = key.split(".")
        new_parts: list[
            str
        ] = []  # List to store the transformed key parts with new indices
        current_path: list[str] = []  # This will track the current path as we build it

        # Iterate over each part of the key
        for part in parts:
            # Check if the current part is a numeric index (as string)
            if part.isdigit():
                # Join the current path to form the parent key (before this numeric part)
                parent: str = ".".join(current_path)

                # If this numeric part hasn't been seen under the current parent, assign the next available index
                if part not in index_map[parent]:
                    new_index: int = counter_map[
                        parent
                    ]  # Get the next index for this parent
                    index_map[parent][part] = (
                        new_index  # Update the mapping for this part under the parent
                    )
                    counter_map[parent] += 1  # Increment the counter for the next index
                else:
                    # If the numeric part has already been encountered, retrieve the existing index
                    new_index = index_map[parent][part]

                # Add the new index to the new parts list and update the current path
                new_parts.append(str(new_index))
                current_path.append(str(new_index))
            else:
                # If the part is not a number, just add it to the new parts and current path
                new_parts.append(part)
                current_path.append(part)

        # Reassemble the transformed key with the new parts
        new_key: str = ".".join(new_parts)
        # Assign the value to the new key in the new data dictionary
        new_data[new_key] = value

    return new_data


def dict_normalize_indexed_keys(data):
    """
    Normalize keys with indices across all dictionaries in the list,
    ensuring that similar keys without an index are indexed as 0.
    """
    result = []

    for item in data:
        # Create a copy to avoid modifying the original dictionary
        normalized_item = item.copy()

        # Find all keys with an index (e.g., 'Jumper.0')
        indexed_keys = [key for key in item.keys() if re.search(r"\.\d+$", key)]

        for indexed_key in indexed_keys:
            # Extract the key part before the index
            base_key = re.sub(r"\.\d+$", "", indexed_key)

            # If the base key exists without an index, set it as index 0
            if base_key in item and f"{base_key}.0" not in normalized_item:
                normalized_item[f"{base_key}.0"] = item[base_key]

        # Append the normalized dictionary to the result list
        result.append(normalized_item)

    return result
