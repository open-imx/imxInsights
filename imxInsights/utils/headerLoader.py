from collections.abc import Callable
from dataclasses import dataclass, field

import pandas as pd
from pandas.io.formats.style import Styler
from xlsxwriter.worksheet import Worksheet  # type: ignore

# TODO: first column is now Field, we should rename it to Column metadata and fill all row in table gray to make clear we not filling the rows.


class HeaderLoader:
    """
    Class to handle the lookup of data for the header rows of a sheet
    """

    def __init__(self, headerfile, pathfield, ignore=tuple()):
        self.spec = pd.read_csv(
            headerfile,
            on_bad_lines="skip",
            encoding="utf-8",
        )
        for col in self.spec.columns:
            if col + "_link" in self.spec.columns:
                self.spec[col] = (
                    '=HYPERLINK("'
                    + self.spec[col + "_link"]
                    + '", "'
                    + self.spec[col]
                    + '")'
                )
                self.spec = self.spec.drop([col + "_link"], axis="columns")

        self.spec = self.spec.drop(
            ignore, axis="columns", errors="ignore"
        ).drop_duplicates()
        self.pathfield = pathfield

    @staticmethod
    def remove_extra_path(s):
        if "->" in s:
            # This happens for paths that changed, for example InitialSituation->newsituation
            # We use the new situation
            s = s.partition("->")[2].strip()

        if s.startswith("++") or s.startswith("--"):
            s = s[2:].strip()

        if s.lower().startswith("imspoor"):
            s = ".".join(s.split(".")[1:])

        return s

    @staticmethod
    def remove_numeric(s):
        return ".".join(part for part in s.split(".") if not part.isnumeric())

    def add_header_to_sheet(self, df):
        """
        Adds a specification header block to the top of the given DataFrame for Excel export.

        The final DataFrame includes:
        - A header block containing specification information.
        - The original DataFrame rows.
        - Columns are reordered based on predefined logic.

        Args:
            df (pandas.DataFrame): The DataFrame to which the header information should be added.

        Returns:
            pandas.DataFrame: The modified DataFrame with specification header rows prepended.
        """

        # TODO: check if we can use pandas metadata to add column metadata!

        basepath = self.remove_extra_path(df["path_to_root"].values[0]) + "."

        # Info values that are relavent for this frame
        rel_spec = self.spec[self.spec[self.pathfield].str.startswith(basepath)].copy()
        rel_spec["field"] = rel_spec[self.pathfield].str.slice(start=len(basepath))

        # Column names as present in the frame
        from_frame = pd.DataFrame({"field": df.columns})
        from_frame["path"] = (basepath + from_frame.field).map(self.remove_numeric)

        # We match on path, as this is the path without numeric parts
        # However, we keep the field names with the numeric part if present.
        # If a field is not present then it will be filled form the CSV file.

        info1 = pd.merge(
            rel_spec, from_frame, how="left", left_on=self.pathfield, right_on="path"
        )
        info1["field"] = info1["field_y"].fillna(info1["field_x"])
        info1.index = info1.field
        info1 = info1.drop(
            ["field_x", "field_y", "field", self.pathfield, "path"],
            axis="columns",
            errors="ignore",
        )

        # At this point all normal fields should be populated in the info frame.
        # We might be missing extention objects
        # for this we check if any of the field names are present as full paths in the spec
        # TODO test with big file
        info2 = pd.merge(
            from_frame, self.spec, how="inner", left_on="field", right_on=self.pathfield
        )
        info2.index = info2.field
        info2 = info2.drop(
            ["field", "path_y", "path_x", self.pathfield, "path"],
            axis="columns",
            errors="ignore",
        )

        info = pd.concat([info1, info2]).transpose().dropna(how="all")

        # TODO: add info for display and analyse collumns

        # Add the index as an actual collumn at the start
        labels = pd.DataFrame({"Field": info.index})
        labels = labels.set_index(labels.Field)
        info = pd.concat([labels, info], axis="columns")

        # Ordering:
        # 1. Fields
        # 2. Added by imxInsights != |display
        # 3. all fields in order
        # 4. all extentions
        # 5. path to root
        def col_key(colname):
            base_fields = [
                "@puic",
                "parent",
                "children",
                "@name",
                "path",
                "tag",
                "status",
                "geometry_status",
            ]
            if colname == "Field":
                return (0, colname)
            if not colname.strip():
                return (5, 0)
            if colname in base_fields:
                return (1, base_fields.index(colname))
            if colname == "path_to_root":
                return (99, colname)
            is_extention_code = 3 if colname.startswith(".extension") else 2
            if "|" in colname:
                return (is_extention_code, colname.partition("|")[0], 1)
            else:
                return (is_extention_code, colname, 0)

        all_columns = list(set(info.columns.to_list()) | set(df.columns.to_list()))
        in_order = sorted(all_columns, key=col_key)

        # Hack together the order
        ordering_df = pd.DataFrame(columns=in_order)

        return pd.concat([ordering_df, info, df])

    @staticmethod
    def write_df_and_header_to_sheet(
        writer,
        sheet_name: str,
        df: pd.DataFrame | Styler,
        *,
        write_index: bool = False,
        header: bool = True,
        auto_filter: bool = True,
        styler_fn: Callable | None = None,
    ) -> Worksheet:
        """
        Write a DataFrame or Styler object to an Excel sheet, preserving documentation rows
        at the top and optionally applying styling and autofilter.

        Args:
            writer: An ExcelWriter object used to write the Excel file.
            sheet_name (str): Name of the worksheet where the data will be written.
            df (pd.DataFrame or Styler): The DataFrame or Styler object to write to the sheet.
            index (bool, optional): Whether to write row indices. Defaults to False.
            header (bool, optional): Whether to write column headers. Defaults to True.
            auto_filter (bool, optional): Whether to apply autofilter to the data rows. Defaults to True.
            styler_fn (callable, optional): Optional function to apply styling to the data (not documentation) rows. Defaults to None.

        Returns:
            Worksheet: The xlsxwriter Worksheet object for the written sheet.
        """
        documentation_indicator = df.index.to_series().apply(
            lambda x: isinstance(x, str)
        )

        documentation = df[documentation_indicator]

        documentation_size = len(documentation)
        documentation.to_excel(
            writer,
            sheet_name=sheet_name,
            index=write_index,
            header=False,
        )
        worksheet = writer.sheets[sheet_name]

        # styling all specification rows
        spec_format_dict = {
            "bg_color": "#d1d1d1",
            "valign": "top",
            "align": "left",
            "num_format": "@",
            "locked": True,
            "border": 7,
            "text_wrap": True,
        }
        writer.spec_format = writer.book.add_format(spec_format_dict)

        spec_format = writer.spec_format

        for index, row in df[documentation_indicator].iterrows():
            row_num = df.index.get_loc(index)
            worksheet.set_row(row_num, 15.0001, spec_format)

        # now write body
        body = df[~documentation_indicator]

        styler = styler_fn(body)

        styler.to_excel(
            writer,
            sheet_name=sheet_name,
            index=write_index,
            header=header,
            startrow=documentation_size,
        )

        worksheet.freeze_panes(documentation_size + 1, 1)
        worksheet.documentation_size = documentation_size
        worksheet.documentation_indicator = documentation_indicator

        data = df.data if isinstance(df, Styler) else df  # type: ignore

        # TODO: should be report helper
        if auto_filter and not data.empty:
            num_cols = len(data.columns) - 1
            worksheet.autofilter(documentation_size, 0, documentation_size, num_cols)

        # TODO: should be report helper
        for i, column in enumerate(df.columns):
            # Include the collumn name not rest of header, also minimal 15 chars wide
            col_data = df[column].iloc[documentation_size:]
            max_len_in_col = max(
                col_data.astype(str).map(len).max(), len(str(column)), 15
            )
            # Always show the whole column name
            max_allowed = max(80, len(str(column)))
            new_width = min(max_len_in_col, max_allowed)
            worksheet.set_column(i, i, new_width + 2)

        return worksheet


@dataclass
class HeaderSpec:
    file_path: str
    path_field: str = "path"

    # TODO: tuples as a datatype are nice, but lists are used for most features... we should keep it constant

    ignore_fields: tuple[str] = field(default_factory=tuple)

    def get_loader(self) -> "HeaderLoader":
        return HeaderLoader(
            self.file_path,
            self.path_field,
            ignore=self.ignore_fields,
        )
