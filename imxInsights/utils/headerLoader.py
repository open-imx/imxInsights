from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pandas.io.formats.style import Styler
from xlsxwriter.worksheet import Worksheet  # type: ignore

from imxInsights.utils.report_helpers import autosize_columns, apply_autofilter


class HeaderLoader:
    """
    Class to handle the lookup and processing of metadata header rows for Excel sheets.

    Responsibilities:
    - Load a CSV specification file containing metadata about fields.
    - Clean and normalize paths in the specification (removing indices, prefixes, diff symbols).
    - Map specification metadata onto DataFrame columns.
    - Prepend metadata rows as "header blocks" above data rows in exported Excel files.
    - Write styled metadata + data blocks into Excel sheets.

    This is typically used to enrich exported Excel reports with structured
    documentation rows at the top, making the meaning of each column explicit.
    """

    def __init__(
        self,
        spec_csv_path: str | Path,
        spec_path_col: str,
        spec_ignore_cols: list[str] = [],
    ):
        """
        Initialize a HeaderLoader.

        Args:
            spec_csv_path (str | Path): Path to a CSV file containing header specifications.
            spec_path_col (str): Column name in the spec file containing path references.
            spec_ignore_cols (list[str], optional): List of columns to ignore and drop from the specification.
        """
        self.spec_csv_path: Path = (
            spec_csv_path if isinstance(spec_csv_path, Path) else Path(spec_csv_path)
        )
        self.spec_path_col = spec_path_col
        self.spec_ignore_cols: list[str] = spec_ignore_cols
        self.metadata_label_col = "Tester"

        # Load specification table
        self.spec_df = pd.read_csv(self.spec_csv_path, on_bad_lines="skip", encoding="utf-8")

        # Normalize spec file by applying transformations
        self._apply_hyperlink_columns()
        self._drop_ignored_and_duplicates()

    def _apply_hyperlink_columns(self):
        """
        Convert any pair of (column, column_link) into Excel HYPERLINK formulas.

        Example:
            If spec has columns `name` and `name_link`, then replace `name`
            with =HYPERLINK(name_link, name) and drop `name_link`.
        """
        for col in self.spec_df.columns:
            link_col = f"{col}_link"
            if link_col in self.spec_df.columns:
                self.spec_df[col] = (
                    '=HYPERLINK("'
                    + self.spec_df[link_col]
                    + '", "'
                    + self.spec_df[col]
                    + '")'
                )
                self.spec_df = self.spec_df.drop([link_col], axis="columns")

    def _drop_ignored_and_duplicates(self):
        """
        Drop ignored columns from the spec file and remove duplicate rows.
        """
        self.spec_df = self.spec_df.drop(
            self.spec_ignore_cols, axis="columns", errors="ignore"
        ).drop_duplicates()

    @staticmethod
    def _clean_path(s: str) -> str:
        """
        Clean a path string for comparison with the specification.

        Removes:
        - Diff symbols ('->', '++', '--').
        - Leading 'imspoor' root.
        """
        if "->" in s:
            s = s.partition("->")[2].strip()
        if s.startswith("++") or s.startswith("--"):
            s = s[2:].strip()
        if s.lower().startswith("imspoor"):
            s = ".".join(s.split(".")[1:])
        return s

    @staticmethod
    def _normalize_path_without_indices(s: str) -> str:
        """
        Remove numeric indices from a dotted path string.

        Example:
            'extension.MicroNode.0.@railConnectionRef'
            -> 'extension.MicroNode.@railConnectionRef'
        """
        return ".".join(part for part in s.split(".") if not part.isnumeric())

    def _get_specs_for_object(self, object_base_path: str) -> pd.DataFrame:
        """
        Extract a subset of the specification relevant to a given object base path.

        Args:
            object_base_path (str): Path prefix to filter specification rows.

        Returns:
            pd.DataFrame: Specification rows starting with the given path.
        """
        object_specs_df = self.spec_df[
            self.spec_df[self.spec_path_col].str.startswith(object_base_path)
        ].copy()
        object_specs_df["field"] = object_specs_df[self.spec_path_col].str.slice(
            start=len(object_base_path)
        )
        return object_specs_df

    def _build_column_path_map(self, df: pd.DataFrame, object_base_path: str) -> pd.DataFrame:
        """
        Construct paths for each DataFrame column relative to a base path.

        Args:
            df (pd.DataFrame): DataFrame with actual data columns.
            object_base_path (str): Path prefix to prepend to columns.

        Returns:
            pd.DataFrame: Mapping of DataFrame columns to normalized spec paths.
        """
        column_path_map_df = pd.DataFrame({"field": df.columns})
        column_path_map_df["path"] = (object_base_path + column_path_map_df["field"]).map(
            self._normalize_path_without_indices
        )
        return column_path_map_df

    def _build_metadata_header(
        self, object_specs_df: pd.DataFrame, column_path_map_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Map specification metadata onto DataFrame columns to build a metadata header.

        See workflow in code comments for merge logic.

        Returns:
            pd.DataFrame: Transposed metadata header with fields as columns.
        """
        # Merge object specs with actual frame (align spec paths with actual data paths)
        merged_specs_df = pd.merge(
            object_specs_df,
            column_path_map_df,
            how="left",
            left_on=self.spec_path_col,
            right_on="path",
        )

        # Prefer 'field' from actual data when available, else fall back to spec-derived field
        merged_specs_df["field"] = merged_specs_df["field_y"].fillna(merged_specs_df["field_x"])

        # Index by 'field' for alignment
        merged_specs_df = merged_specs_df.set_index("field", drop=False)

        # Drop redundant merge helper columns
        merged_specs_df = merged_specs_df.drop(
            ["field_x", "field_y", "field", self.spec_path_col, "path"],
            axis="columns",
            errors="ignore",
        )

        # Handle extension objects via direct matches on full paths in the spec
        direct_match_specs_df = pd.merge(
            column_path_map_df,
            self.spec_df,
            how="inner",
            left_on="field",
            right_on=self.spec_path_col,
        )

        # Index by 'field' for alignment
        direct_match_specs_df = direct_match_specs_df.set_index("field", drop=False)

        # Drop unnecessary merge helper columns
        direct_match_specs_df = direct_match_specs_df.drop(
            ["field", "path_y", "path_x", self.spec_path_col, "path"],
            axis="columns",
            errors="ignore",
        )

        # Combine both results, transpose so fields become columns, and drop all-NaN rows
        metadata_header_df = pd.concat([merged_specs_df, direct_match_specs_df]).transpose().dropna(
            how="all"
        )

        return metadata_header_df

    def _merge_metadata_and_data(
        self, df: pd.DataFrame, metadata_header_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge metadata info into a DataFrame and reorder columns.

        Args:
            df (pd.DataFrame): The input data frame with actual values.
            metadata_header_df (pd.DataFrame): Metadata header with specification info.

        Returns:
            pd.DataFrame: DataFrame containing metadata rows stacked on top
            of the original data rows, with consistent column ordering.
        """

        def col_key(colname: str):
            """
            Define a custom sort order for DataFrame columns.

            Ordering rules (priority-based):
            1. The label column (self.metadata_label_col) always comes first.
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

            # Ensure the label column is always first
            if colname == self.metadata_label_col:
                return (0, colname)

            # Handle empty column names (rare case, force to the end)
            if not str(colname).strip():
                return (5, 0)

            # Base fields in defined order
            if colname in base_fields:
                return (1, base_fields.index(colname))

            # path_to_root is always last
            if colname == "path_to_root":
                return (99, colname)

            # Distinguish between extension and regular fields
            is_extension_code = 3 if str(colname).startswith(".extension") else 2

            # If the field contains a "|" it means it is an "augmented" or derived column
            if "|" in str(colname):
                return (is_extension_code, str(colname).partition("|")[0], 1)
            else:
                return (is_extension_code, str(colname), 0)

        # Build the metadata dataframe with the label as both index and column
        metadata_label_df = pd.DataFrame({self.metadata_label_col: metadata_header_df.index})
        metadata_label_df = metadata_label_df.set_index(metadata_label_df[self.metadata_label_col])

        # Prepend the labels to the metadata header (ensures label column is present)
        metadata_header_df = pd.concat([metadata_label_df, metadata_header_df], axis="columns")

        # Compute the complete set of columns from both metadata and dataframes
        combined_cols = list(
            set(metadata_header_df.columns.to_list()) | set(df.columns.to_list())
        )

        # Apply the custom sorting logic
        ordered_cols = sorted(combined_cols, key=col_key)

        # Prepare an empty dataframe to enforce column ordering
        empty_ordering_df = pd.DataFrame(columns=ordered_cols)

        # Concat ensures consistent columns + merges metadata & dataframes
        return pd.concat([empty_ordering_df, metadata_header_df, df])

    def apply_metadata_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add a specification header block on top of the given DataFrame.

        Args:
            df (pd.DataFrame): DataFrame with data rows and at least a 'path_to_root' column.

        Returns:
            pd.DataFrame: Combined DataFrame with metadata header rows prepended.
        """
        object_base_path = self._clean_path(df["path_to_root"].values[0]) + "."
        object_specs_df = self._get_specs_for_object(object_base_path=object_base_path)
        column_path_map_df = self._build_column_path_map(df=df, object_base_path=object_base_path)
        metadata_header_df = self._build_metadata_header(
            object_specs_df=object_specs_df, column_path_map_df=column_path_map_df
        )

        # TODO: check if we can use pandas metadata to add column metadata!
        # TODO: add info for display and analyse columns

        df_with_header = self._merge_metadata_and_data(df=df, metadata_header_df=metadata_header_df)
        return df_with_header

    @staticmethod
    def to_excel_with_metadata(
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
        Write a DataFrame or Styler to an Excel worksheet, including metadata header rows.

        The header rows are styled in gray and frozen, while the data block
        may have styling applied through a custom styler function.

        Args:
            writer: An ExcelWriter object.
            sheet_name (str): Target worksheet name.
            df (pd.DataFrame | Styler): Data or styled DataFrame including metadata rows.
            write_index (bool, optional): Write index column. Default False.
            header (bool, optional): Write column headers. Default True.
            auto_filter (bool, optional): Add an autofilter. Default True.
            styler_fn (Callable, optional): Function applied to style the body rows.

        Returns:
            Worksheet: The created xlsxwriter worksheet object.
        """
        is_metadata_row = df.index.to_series().apply(lambda x: isinstance(x, str))
        metadata_block_df = df[is_metadata_row]

        metadata_rows = len(metadata_block_df)
        metadata_block_df.to_excel(
            writer,
            sheet_name=sheet_name,
            index=write_index,
            header=False,
        )
        worksheet = writer.sheets[sheet_name]

        # Style all specification rows
        metadata_cell_format = {
            "bg_color": "#d1d1d1",
            "valign": "top",
            "align": "left",
            "num_format": "@",
            "locked": True,
            "border": 7,
            "text_wrap": True,
        }
        metadata_format = writer.book.add_format(metadata_cell_format)

        for _, _row in df[is_metadata_row].iterrows():
            xlsx_row_idx = df.index.get_loc(_row.name)
            worksheet.set_row(xlsx_row_idx, 15.0001, metadata_format)

        data_block = df[~is_metadata_row]
        if styler_fn:
            data_block = styler_fn(data_block)

        data_block.to_excel(
            writer,
            sheet_name=sheet_name,
            index=write_index,
            header=header,
            startrow=metadata_rows,
        )

        worksheet.freeze_panes(metadata_rows + 1, 1)

        # Calculate widths and apply filter only to the data area
        data_df = df.data if isinstance(df, Styler) else df  # type: ignore

        if auto_filter and not data_df.empty:
            apply_autofilter(worksheet, start_row=metadata_rows, data_df=data_df)

        autosize_columns(
            worksheet=worksheet,
            full_df=df,
            data_start_row=metadata_rows,
            min_width=15,
            header_min_width=80,
            padding=2,
        )

        return worksheet


@dataclass
class HeaderSpec:
    """
    Dataclass wrapper for header specification files.

    Attributes:
        spec_csv_path (str): Path to the CSV file with header metadata.
        spec_path_col (str): Column name used as path field in the spec file. Default "path".
        spec_ignore_cols (list[str]): List of fields to ignore when loading.

    Methods:
        get_loader() -> HeaderLoader:
            Build and return a `HeaderLoader` instance for this specification.
    """

    spec_csv_path: str
    spec_path_col: str = "path"
    spec_ignore_cols: list[str] = field(default_factory=list)

    def get_loader(self) -> "HeaderLoader":
        """Return a `HeaderLoader` configured with this spec."""
        return HeaderLoader(
            self.spec_csv_path,
            self.spec_path_col,
            spec_ignore_cols=self.spec_ignore_cols,
        )
