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
