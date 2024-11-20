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


# def df_sort_by_list(df: pd.DataFrame, column_order: list[str]) -> pd.DataFrame:
#     """
#     Sort DataFrame by the 'status' column according to a specific order.
#
#     Args:
#         df: The DataFrame to sort.
#         column_order: List of statuses defining the order.
#
#     Returns:
#         The sorted DataFrame.
#     """
#     df["status"] = pd.Categorical(df["status"], categories=column_order, ordered=True)
#     return df.sort_values("status")


class TimelineDataframeBuilder:
    @staticmethod
    def _prepare_df(df: pd.DataFrame):
        """
        Prepares the DataFrame by replacing None and empty values, sorting columns,
        and setting a multi-index.
        """
        # df.replace({None: '<NotPresent>', np.nan: '<NotPresent>', '': '<NotPresent>'}, inplace=True)
        df = df_columns_sort_start_end(
            df, ["container_id", "tag", "imx_situation", "path"], []
        )
        # Set multi-index on '@puic' and 'T'
        df.set_index(["@puic", "T"], inplace=True)
        return df

    @staticmethod
    def _set_mask(df: pd.DataFrame):
        """
        Sets the change mask and applies color styles for changes in the DataFrame.
        """

        def create_change_mask(group, ignore_columns):
            """
            Create a change mask for a DataFrame group (grouped by '@puic').
            Ignores specified columns and marks the first row as not changed.
            """
            # Create the initial change mask
            diff_mask = group != group.shift()

            # Set mask to False for the columns to ignore
            for col in ignore_columns:
                if col in diff_mask.columns:
                    diff_mask[col] = False

            # Ignore the first T (T == 0) since it should not be compared
            diff_mask.loc[group.index.get_level_values("T") == 0] = False
            return diff_mask

        ignore_columns = [
            "@puic",
            "container_id",
            "imx_situation",
        ]  # Modify this list with columns you want to ignore

        # Apply change detection for each '@puic' group
        change_mask = df.groupby(level="@puic").apply(
            lambda group: create_change_mask(group, ignore_columns=ignore_columns)
        )

        # Drop the grouping index to align with the original DataFrame
        change_mask = change_mask.droplevel(0)

        # Apply styling only for the cells where the mask is True
        return df.style.apply(
            lambda x: [
                "color: red" if change_mask.loc[x.name, col] else "" for col in x.index
            ],
            axis=1,
        )

    @staticmethod
    def _style_dataframe(styled_df):
        """
        Apply additional styles such as borders and alternating row background colors.
        """
        # Set borders
        styled_df = styled_df.set_table_styles(
            [
                {"selector": "", "props": [("border", "0.1px solid black")]},
                {"selector": "th", "props": [("border", "0.5px solid black")]},
                {"selector": "td", "props": [("border", "0.5px solid black")]},
            ]
        ).set_properties(**{"text-align": "left"})

        # Set alternating background on multi index level 1
        def style_rows(x):
            styles = pd.DataFrame(
                "", index=x.index, columns=x.columns
            )  # Initialize empty styles DataFrame
            set_background = True  # Flag to alternate styling
            # columns_to_set = ["container_id", "path", "tag"]

            # Loop through unique values in the '@puic' index level
            for value in x.index.get_level_values("@puic").unique():
                # Get the rows corresponding to this value in the index
                rows = x.index.get_loc(value)
                if isinstance(rows, slice):
                    rows = list(range(rows.start, rows.stop))

                # Apply the background color to rows based on the set_background flag
                if set_background:
                    for idx, row in enumerate(rows):
                        if row:
                            styles.iloc[idx] = "background-color: #F2F2F2"
                            # for column in columns_to_set:
                            #     styles.iloc[idx, x.columns.get_loc(column)] = 'background-color: #F2F2F2'

                # Toggle the set_background flag for alternating background color
                set_background = not set_background

            return styles

        styled_df.apply(style_rows, axis=None)
        return styled_df

    @staticmethod
    def get_styled_dataframe(df):
        """
        Prepare the DataFrame, apply the change mask, and return a styled DataFrame.
        """
        df = TimelineDataframeBuilder._prepare_df(df)
        styled_df = TimelineDataframeBuilder._set_mask(df)
        return TimelineDataframeBuilder._style_dataframe(styled_df)

    # @staticmethod
    # def to_html(df, filename="grouped.html"):
    #     """
    #     Generate an HTML representation of the styled DataFrame.
    #     """
    #     styled_df = TimelineDataframeBuilder.get_styled_dataframe(df)
    #     styled_df.to_html(filename)
    #
    # @staticmethod
    # def to_excel(df, filename="imx_timeline_df.xlsx", sheet_name="time_line"):
    #     """
    #     Generate an Excel file with the styled DataFrame.
    #     """
    #     styled_df = TimelineDataframeBuilder.get_styled_dataframe(df)
    #     writer = pd.ExcelWriter(filename, engine='xlsxwriter')
    #     styled_df.to_excel(writer, sheet_name=sheet_name)
    #     worksheet = writer.sheets[sheet_name]
    #     worksheet.freeze_panes(1, 5)
    #     worksheet.set_column(2, 4, None, None, {"level": 1, "hidden": True})
    #     worksheet.autofit()
    #     writer.close()


#
# if __name__ == "__main__":
#     # Example usage:
#     data = {
#         '@puic': [
#             'dd572e7e-ee91-45c3-950a-f6457c1758c9', 'dd572e7e-ee91-45c3-950a-f6457c1758c9',
#             'dd572e7e-ee91-45c3-950a-f6457c1758c9', 'cb464fca-ac53-4f4f-b289-3445ca8a8497',
#             'cb464fca-ac53-4f4f-b289-3445ca8a8497', 'cb464fca-ac53-4f4f-b289-3445ca8a8497',
#             '167c4d68-3b65-47d6-9dbc-a5f43056b693', '167c4d68-3b65-47d6-9dbc-a5f43056b693',
#             '167c4d68-3b65-47d6-9dbc-a5f43056b693'
#         ],
#         'path': ['CivilConstruction', 'CivilConstruction', 'Bridge', 'CivilConstruction',
#                  'CivilConstruction', 'Bridge', 'CivilConstruction', 'CivilConstruction', 'Bridge'],
#         'T': [0, 1, 2, 0, 1, 2, 0, 1, 2],
#         'container_id': ['1bb74e8f-b33d-4713-b5cb-f8a2a6a4cdac', '60f81d78-3bb9-40f2-bdae-5ede79830ebc',
#                          'fe539e28-0128-42b7-9c8a-5f4bcf52426a', '1bb74e8f-b33d-4713-b5cb-f8a2a6a4cdac',
#                          '60f81d78-3bb9-40f2-bdae-5f4bcf52426a', 'fe539e28-0128-42b7-9c8a-5f4bcf52426a',
#                          '1bb74e8f-b33d-4713-b5cb-f8a2a6a4cdac', '60f81d78-3bb9-40f2-bdae-5f4bcf52426a',
#                          'fe539e28-0128-42b7-9c8a-5f4bcf52426a'],
#         'imx_situation': ['InitialSituation', 'NewSituation', '', 'InitialSituation', 'NewSituation', '',
#                           'InitialSituation', 'NewSituation', ''],
#         'tag': ['CivilConstruction', 'CivilConstruction', 'Bridge', 'CivilConstruction', 'CivilConstruction',
#                 'Bridge', 'CivilConstruction', 'CivilConstruction', 'Bridge']
#     }
#     df = pd.DataFrame(data)
#
#     # Call the methods directly as class methods
#     styled_df = TimelineDataframeBuilder.get_styled_dataframe(df)
#     TimelineDataframeBuilder.to_html(df, "grouped.html")
#     TimelineDataframeBuilder.to_excel(df, "imx_timeline.xlsx")
