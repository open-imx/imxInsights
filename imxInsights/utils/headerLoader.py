from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pandas.io.formats.style import Styler
from xlsxwriter.worksheet import Worksheet  # type: ignore

# TODO: first column is now Field, we should rename it to Column metadata and fill all row in table gray to make clear we not filling the rows.


class HeaderLoader:
    """
    Class to handle the lookup of data for the header rows of a sheet
    """

    def __init__(
        self, header_file: str | Path, path_field: str, ignore_columns: list[str] = []
    ):
        self.header_file: Path = (
            header_file if isinstance(header_file, Path) else Path(header_file)
        )
        self.path_field = path_field
        self.ignore_columns: list[str] = ignore_columns
        self.field_column_name = "Tester"
        self.spec = pd.read_csv(header_file, on_bad_lines="skip", encoding="utf-8")
        self._create_hyperlink()
        self._remove_ignored_columns()

    def _create_hyperlink(self):
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

    def _remove_ignored_columns(self):
        self.spec = self.spec.drop(
            self.ignore_columns, axis="columns", errors="ignore"
        ).drop_duplicates()

    @staticmethod
    def _clean_path(s):
        """We need to remove imspoor root, `->`, `++` or `--` (used in diff reports) and get the new value"""
        if "->" in s:
            s = s.partition("->")[2].strip()
        if s.startswith("++") or s.startswith("--"):
            s = s[2:].strip()
        if s.lower().startswith("imspoor"):
            s = ".".join(s.split(".")[1:])
        return s

    @staticmethod
    def _remove_numeric_from_path(s):
        """We do not have indexes in the specification path, we need to remove them to get the correct specs."""
        return ".".join(part for part in s.split(".") if not part.isnumeric())

    def _get_object_specs(self, base_path: str) -> pd.DataFrame:
        rel_spec = self.spec[
            self.spec[self.path_field].str.startswith(base_path)
        ].copy()
        rel_spec["field"] = rel_spec[self.path_field].str.slice(start=len(base_path))
        return rel_spec

    def _get_columns_spec_paths(self, df: pd.DataFrame, base_path: str):
        from_frame = pd.DataFrame({"field": df.columns})
        from_frame["path"] = (base_path + from_frame.field).map(
            self._remove_numeric_from_path
        )
        return from_frame

    def _map_specs_on_df_get_metadata_header(
        self, object_specs: pd.DataFrame, from_frame: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Map the object specifications onto an existing dataframe to produce a metadata header dataframe.

        Workflow:
        - Start from two sources:
            * `object_specs`: expected specification of fields (paths without numeric indices).
            * `from_frame`: dataframe extracted from actual input data (fields may include numbers).
        - Merge them to align paths, but keep original field names with numbers if present.
        - Handle extension objects separately (they may only appear in `spec`).
        - Combine both results into a single metadata header dataframe.

        Returns:
            A transposed dataframe where columns correspond to metadata attributes for each field in the dataset.
        """

        # merge object specs with actual frame
        #  - Match on `path_field` vs. `path`.
        #  - This ensures we align specification paths with actual data paths.
        info1 = pd.merge(
            object_specs,
            from_frame,
            how="left",
            left_on=self.path_field,
            right_on="path",
        )

        # If the merge produced both field_x and field_y:
        # - field_y comes from `from_frame` (actual CSV/Excel input)
        # - field_x comes from `object_specs` (reference spec)
        # Use field_y if available, otherwise fall back to field_x
        info1["field"] = info1["field_y"].fillna(info1["field_x"])

        # Make 'field' the index for easy alignment later
        info1 = info1.set_index("field", drop=False)

        # Drop redundant merge helper columns we don’t need anymore
        info1 = info1.drop(
            ["field_x", "field_y", "field", self.path_field, "path"],
            axis="columns",
            errors="ignore",
        )

        # handle extension objects
        #  - Some fields may not be in object_specs but exist as full paths in self.spec.
        #  - For those, merge from_frame with self.spec on field vs. path_field.
        info2 = pd.merge(
            from_frame,
            self.spec,
            how="inner",
            left_on="field",
            right_on=self.path_field,
        )

        # index by field for alignment
        info2 = info2.set_index("field", drop=False)

        # Drop unnecessary merge helper columns
        info2 = info2.drop(
            ["field", "path_y", "path_x", self.path_field, "path"],
            axis="columns",
            errors="ignore",
        )

        # --- Combine both results ---
        # Concatenate metadata from both merges along the rows,
        # then transpose so that fields become columns.
        # Drop columns where all values are NaN (useless metadata).
        info = pd.concat([info1, info2]).transpose().dropna(how="all")

        return info

    def _add_info_to_df(self, df: pd.DataFrame, info: pd.DataFrame) -> pd.DataFrame:
        """Merge metadata info into a dataframe and ensure consistent column ordering."""

        def col_key(colname: str):
            """
            Define a custom sort order for DataFrame columns.

            Ordering rules (priority-based):
            1. The 'field' column (self.field_column_name) always comes first.
            2. Standard base fields (e.g. puic, parent, children, etc.) come next,
               in the order they are listed.
            3. Columns automatically added by imxInsights (containing '|') come after base fields.
            4. Extension fields (starting with '.extension') follow after regular fields.
            5. Any completely unknown/unmatched fields get pushed to the end.
            6. Finally, "path_to_root" is explicitly placed at the very end.
            """
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

            # Ensure the field column is always first
            if colname == self.field_column_name:
                return (0, colname)

            # Handle empty column names (rare case, force to the end)
            if not colname.strip():
                return (5, 0)

            # Base fields in defined order
            if colname in base_fields:
                return (1, base_fields.index(colname))

            # path_to_root is always last
            if colname == "path_to_root":
                return (99, colname)

            # Distinguish between extension and regular fields
            is_extension_code = 3 if colname.startswith(".extension") else 2

            # If the field contains a "|" it means it is an "augmented" or derived column
            if "|" in colname:
                return (is_extension_code, colname.partition("|")[0], 1)
            else:
                return (is_extension_code, colname, 0)

        # Build the metadata dataframe with the 'field' as both index and column

        # Create a labels dataframe with the index (fields) as an explicit column.
        labels = pd.DataFrame({self.field_column_name: info.index})
        labels = labels.set_index(labels[self.field_column_name])

        # Prepend the labels to the info dataframe (ensures field column is present)
        info = pd.concat([labels, info], axis="columns")

        # Compute the complete set of columns from both info and dataframes
        all_columns = list(set(info.columns.to_list()) | set(df.columns.to_list()))

        # Apply the custom sorting logic
        in_order = sorted(all_columns, key=col_key)

        # Prepare an empty dataframe to enforce column ordering
        ordering_df = pd.DataFrame(columns=in_order)

        # concat: ensures consistent columns + merges metadata & dataframes
        return pd.concat([ordering_df, info, df])

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

        base_path = self._clean_path(df["path_to_root"].values[0]) + "."
        object_specs = self._get_object_specs(base_path=base_path)
        from_frame = self._get_columns_spec_paths(df=df, base_path=base_path)
        info = self._map_specs_on_df_get_metadata_header(
            object_specs=object_specs, from_frame=from_frame
        )

        # TODO: check if we can use pandas metadata to add column metadata!

        # TODO: add info for display and analyse columns

        full_df = self._add_info_to_df(df=df, info=info)
        return full_df

    @staticmethod
    def write_df_and_header_to_sheet(
        writer,
        sheet_name: str,
        df: pd.DataFrame,
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

        body = df[~documentation_indicator]

        if styler_fn:
            body = styler_fn(body)

        body.to_excel(
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
    ignore_fields: list[str] = field(default_factory=list)

    def get_loader(self) -> "HeaderLoader":
        return HeaderLoader(
            self.file_path,
            self.path_field,
            ignore_columns=self.ignore_fields,
        )
