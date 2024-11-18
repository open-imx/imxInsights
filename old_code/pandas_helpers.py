import pandas as pd


def styler_highlight_changes(value: str) -> str:
    """
    Highlight changes in a DataFrame cell with different borders based on the value.

    Args:
        value: The value of the cell to be styled.

    Returns:
        The CSS style string for highlighting.
    """
    if str(value).startswith("++"):
        return "border: 2px solid red;"
    elif str(value).startswith("--"):
        return "border: 2px solid blue;"
    elif "->" in str(value):
        return "border: 2px solid green;"
    else:
        return ""


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
    remaining_columns = [
        col for col in df.columns if col not in front_columns_present + end_columns
    ]
    return df[front_columns_present + sorted(remaining_columns) + sorted(end_columns)]


def df_sort_by_list(df: pd.DataFrame, column_order: list[str]) -> pd.DataFrame:
    """
    Sort DataFrame by the 'status' column according to a specific order.

    Args:
        df: The DataFrame to sort.
        column_order: List of statuses defining the order.

    Returns:
        The sorted DataFrame.
    """
    df["status"] = pd.Categorical(df["status"], categories=column_order, ordered=True)
    return df.sort_values("status")
