import pandas as pd


def styler_highlight_changes(value: str, borders=False) -> str:  # pragma: no cover
    """
    Highlight changes in a DataFrame cell with different borders based on the value.

    Args:
        value: The value of the cell to be styled.
        borders: borders instead of text color

    Returns:
        The CSS style string for highlighting.
    """
    if borders:
        if str(value).startswith("++"):
            return "border: 2px solid red;"
        elif str(value).startswith("--"):
            return "border: 2px solid blue;"
        elif "->" in str(value):
            return "border: 2px solid green;"
        else:
            return ""

    if str(value).startswith("++"):
        return "color: red; font-weight: bold;"
    elif str(value).startswith("--"):
        return "color: blue; font-weight: bold;"
    elif "->" in str(value):
        return "color: green; font-weight: bold;"
    else:
        return ""


def styler_highlight_change_status(value: str) -> str:  # pragma: no cover
    """
    Highlight changes in a DataFrame cell with change status.

    Args:
        value: The value of the cell to be styled.

    Returns:
        The CSS style string for highlighting.
    """
    if str(value) == "added":
        return "color: red; font-weight: bold;"
    elif str(value) == "changed":
        return "color: green; font-weight: bold;"
    elif str(value) == "removed":
        return "color: blue; font-weight: bold;"
    return ""


def style_puic_groups(df):  # pragma: no cover
    styles = pd.DataFrame("", index=df.index, columns=df.columns)
    last_value = None

    for i in range(len(df)):
        if df["@puic"].iloc[i] != last_value:
            styles.iloc[i, :] = "border-top: 2px solid black;"
        last_value = df["@puic"].iloc[i]

    return styles


def df_columns_sort_start_end(
    df: pd.DataFrame, columns_to_front: list[str], end_columns: list[str]
) -> pd.DataFrame:
    """
    Reorder DataFrame columns by placing specified columns at the front and end.

    Args:
        df: The DataFrame to reorder.
        columns_to_front: List of column names to place at the front.
        end_columns: List of column names to place at the end.

    Returns:
        The DataFrame with reordered columns.
    """
    front_columns_present = [col for col in columns_to_front if col in df.columns]
    end_columns_present = [col for col in end_columns if col in df.columns]
    remaining_columns = [
        col
        for col in df.columns
        if col not in front_columns_present + end_columns_present
    ]
    return df[
        front_columns_present + sorted(remaining_columns) + sorted(end_columns_present)
    ]
