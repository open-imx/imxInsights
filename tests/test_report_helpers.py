import pytest
import pandas as pd


from imxInsights.utils.excel_helpers import shorten_sheet_name
from imxInsights.utils.pandas_helpers import df_columns_sort_start_end


def test_shorten_sheet_name():
    assert shorten_sheet_name("ShortName") == "shortname"

    assert (
            shorten_sheet_name("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234")
            == "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234".lower()
    )

    assert (
            shorten_sheet_name("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
            == "ABCDEFGHIJKLMN...WXYZ1234567890".lower()
    )

    assert (
            shorten_sheet_name("123456789012345678901234567890123")
            == "12345678901234...01234567890123".lower()
    )

    assert (
            shorten_sheet_name("Sheet_with_very_long_🚀_name_that_needs_shortening")
            == "Sheet_with_ver...eds_shortening".lower()
    )

    assert shorten_sheet_name("") == ""


def test_df_columns_sort_start_end():
    # Sample DataFrame
    data = {
        "B": [2, 3, 4],
        "A": [1, 2, 3],
        "C": [5, 6, 7],
        "D": [8, 9, 10],
    }
    df = pd.DataFrame(data)

    columns_to_front = ["A"]
    end_columns = ["D"]

    expected_columns = ["A", "B", "C", "D"]

    sorted_df = df_columns_sort_start_end(df, columns_to_front, end_columns)

    assert list(sorted_df.columns) == expected_columns

    df_missing = df.drop(columns=["A"])
    sorted_df_missing = df_columns_sort_start_end(df_missing, columns_to_front, end_columns)
    expected_columns_missing = ["B", "C", "D"]  # A is missing, B and C should be sorted
    assert list(sorted_df_missing.columns) == expected_columns_missing

    sorted_df_no_specified = df_columns_sort_start_end(df, ["X", "Y"], ["Z"])
    expected_columns_no_specified = sorted(df.columns)  # Since no specified columns exist, it should just sort
    assert list(sorted_df_no_specified.columns) == expected_columns_no_specified
