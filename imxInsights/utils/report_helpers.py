import importlib.metadata
import os
import tempfile
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl import load_workbook
from openpyxl.styles import NamedStyle, PatternFill
from pandas.io.formats.style import Styler
from xlsxwriter.worksheet import Worksheet  # type: ignore


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


def app_info_df(process_data: dict) -> pd.DataFrame:
    app_info = {
        "App Name": "ImxInsights",
        "Version": importlib.metadata.version("imxInsights"),
        "Developer": "OpenIMX",
        "Website": "https://open-imx.github.io/imxInsights/",
    }
    disclaimer = "This document is auto-generated. No guarantees are provided regarding the accuracy of the data."
    df = pd.DataFrame(list(app_info.items()), columns=["Attribute", "Value"])
    process_data_df = pd.DataFrame(
        list(process_data.items()), columns=["Attribute", "Value"]
    )

    disclaimer_df = pd.DataFrame({"Attribute": ["Disclaimer"], "Value": [disclaimer]})

    metadata_df = pd.concat(
        [
            df,
            pd.DataFrame([["", ""]]),
            process_data_df,
            pd.DataFrame([["", ""]]),
            disclaimer_df,
        ],
        ignore_index=True,
    )

    return metadata_df


def write_df_to_sheet(
    writer,
    sheet_name: str,
    df: pd.DataFrame | Styler,
    *,
    index: bool = False,
    header: bool = True,
    auto_filter: bool = True,
) -> Worksheet:
    """Write a DataFrame or Styler object to an Excel sheet."""
    df.to_excel(writer, sheet_name=sheet_name, index=index, header=header)
    worksheet = writer.sheets[sheet_name]
    worksheet.autofit()
    worksheet.freeze_panes(1, 0)

    data = df.data if isinstance(df, Styler) else df  # type: ignore

    if auto_filter and not data.empty:
        num_cols = len(data.columns) - 1
        worksheet.autofilter(0, 0, 0, num_cols)
    return worksheet


REVIEW_STYLES = {
    "OK": "80D462",
    "OK met opm": "66FF99",
    "NOK": "FF9999",
    "VRAAG": "F1F98F",
    "Bestaande fout": "FFCC66",
    "Aannemelijk": "E4DFEC",
    "TODO": "F2CEEF",
}


def add_review_styles_to_excel(file_name: str | Path) -> None:
    if isinstance(file_name, Path):
        file_name = f"{file_name}"

    wb = load_workbook(file_name)

    for name, color in REVIEW_STYLES.items():
        style = NamedStyle(name=name)
        style.fill = PatternFill(start_color=color, end_color=color, fill_type="solid")
        if name not in wb.named_styles:
            wb.add_named_style(style)

    temp_file_name = tempfile.mktemp(suffix=".xlsx")
    wb.save(temp_file_name)

    with zipfile.ZipFile(temp_file_name, "r") as zip_in:
        with zipfile.ZipFile(file_name, "w") as zip_out:
            for item in zip_in.infolist():
                data = zip_in.read(item.filename)
                if item.filename == "xl/styles.xml":
                    tree = ET.fromstring(data)
                    ns = {
                        "ns": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"
                    }

                    idx_to_set = []
                    for idx, cell_style in enumerate(
                        tree.findall(".//ns:cellStyle", ns)
                    ):
                        if cell_style.attrib["name"] in REVIEW_STYLES.keys():
                            idx_to_set.append(idx)

                    for idx, cell_xf in enumerate(
                        tree.findall(".//ns:cellStyleXfs/ns:xf", ns)
                    ):
                        if idx in idx_to_set:
                            cell_xf.attrib["applyFont"] = "0"
                            cell_xf.attrib["applyBorder"] = "0"
                            cell_xf.attrib["applyAlignment"] = "0"
                            cell_xf.attrib["applyNumberFormat"] = "0"
                            cell_xf.attrib["applyFill"] = "1"

                    updated_data = ET.tostring(
                        tree, encoding="utf-8", xml_declaration=True
                    )
                    zip_out.writestr(item, updated_data)
                else:
                    zip_out.writestr(item, data)

    if os.path.exists(temp_file_name):
        os.remove(temp_file_name)
