from typing import Any

import pandas as pd


def shorten_sheet_name(sheet_name: str) -> str:
    """
    Shorten the sheet name to fit within 30 characters, adding ellipses in the middle if needed.

    Args:
        sheet_name: The name of the sheet to shorten.

    Returns:
        The shortened sheet name.
    """
    return (
        f"{sheet_name[:14]}...{sheet_name[-14:]}"
        if len(sheet_name) > 30
        else sheet_name
    )


def clean_diff_df(df) -> pd.DataFrame:
    df["@puic"] = df["@puic"].str.lstrip("+-")
    df["tag"] = df["tag"].str.lstrip("+-")
    df["path"] = df["path"].str.lstrip("+-")
    df["parent"] = df["parent"].replace({"++": "", "--": ""})
    df["children"] = df["children"].replace({"++": "", "--": ""})
    return df


def lower_and_index_duplicates(strings: list[str] | set[str]) -> list[str]:
    counts: dict[str, int] = {}
    result: set[str] = set()

    for s in (s.lower() for s in strings):
        counts[s] = counts.get(s, 0) + 1
        result.add(f"{s}{counts[s]}" if counts[s] > 1 else s)

    return sorted(result)


def upper_keys_with_index(original_dict: dict[str, Any]) -> dict[str, Any]:
    new_dict: dict[str, Any] = {}

    for key, value in original_dict.items():
        base_key = key.upper()
        new_key = base_key

        index = 1
        while new_key in new_dict:
            new_key = f"{base_key}_{index}"
            index += 1

        new_dict[new_key] = value

    return new_dict
