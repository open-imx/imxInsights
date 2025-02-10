import pandas as pd


def shorten_sheet_name(sheet_name: str) -> str:
    """
    Shorten the sheet name to fit within 30 characters, adding ellipses in the middle if needed.

    Args:
        sheet_name: The name of the sheet to shorten.

    Returns:
        The shortened sheet name.
    """
    sheet_name = sheet_name.lower()
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
