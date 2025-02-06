import pytest

from imxInsights.utils.excel_helpers import shorten_sheet_name


def test_shorten_sheet_name():
    assert shorten_sheet_name("ShortName") == "ShortName"

    assert (
            shorten_sheet_name("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234")
            == "ABCDEFGHIJKLMNOPQRSTUVWXYZ1234"
    )

    assert (
            shorten_sheet_name("ABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890")
            == "ABCDEFGHIJKLMN...WXYZ1234567890"
    )

    assert (
            shorten_sheet_name("123456789012345678901234567890123")
            == "12345678901234...01234567890123"
    )

    assert (
            shorten_sheet_name("Sheet_with_very_long_🚀_name_that_needs_shortening")
            == "Sheet_with_ver...eds_shortening"
    )

    assert shorten_sheet_name("") == ""


