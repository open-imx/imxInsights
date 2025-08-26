from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from pandas.io.formats.style import Styler
from xlsxwriter.worksheet import Worksheet  # type: ignore

from imxInsights.utils.report_helpers import apply_autofilter, autosize_columns

# TODO: add info for display and analyse columns
# TODO: write index on excel support? and rename index to write_index in write_df_to_sheet
# TODO: Check if we can use pandas metadata to add column metadata!


class HeaderAnnotator:
    """
    Annotates DataFrame exports with metadata headers for Excel reports.

    This class reads a CSV "specification" file describing metadata for fields
    and applies that metadata as annotated header rows when exporting DataFrames
    to Excel. It ensures consistent column ordering and makes reports
    self-documenting.

    !!! danger "Experimental feature"
        HeaderAnnotator and HeaderSpec are experimental and may change without warning.

    Responsibilities:

    - Parse a CSV specification file that defines metadata for fields.
    - Map specification metadata onto DataFrame columns.
    - Prepend metadata rows (header blocks) above data rows in exported Excel files.

    """

    def __init__(
        self,
        spec_csv_path: str | Path,
        spec_path_col: str,
        drop_empty_columns: bool,
        spec_ignore_cols: list[str] | None = None,
    ):
        """
        Initialize a HeaderAnnotator.

        Args:
            spec_csv_path: Path to the CSV file containing header specifications.
            spec_path_col: Column name in the spec that defines the canonical field paths.
            drop_empty_columns: If True, columns with no matching data will be dropped
                from the annotated DataFrame.
            spec_ignore_cols: Optional list of spec columns to ignore and drop.

        Notes:
            - The specification CSV is normalized automatically (duplicate rows dropped,
              hyperlinks applied if *_link columns are present, and known typos corrected).
            - The spec_path_col must contain canonical dot-notation paths (without indices).
        """
        self.spec_csv_path: Path = (
            spec_csv_path if isinstance(spec_csv_path, Path) else Path(spec_csv_path)
        )
        self.spec_path_col = spec_path_col
        self.drop_empty_columns = drop_empty_columns
        self.spec_ignore_cols = spec_ignore_cols or []
        self.metadata_label_col = "IndexInfo"

        # Load specification table
        self.spec_df = pd.read_csv(
            self.spec_csv_path, on_bad_lines="skip", encoding="utf-8"
        )

        ## TODO: BUG IN SPECS SHOULD BE FIXED
        #   - extension is named extention in specs so we should replace
        self.spec_df[self.spec_path_col] = self.spec_df[self.spec_path_col].str.replace(
            "extention", "extension", regex=False
        )

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

    @staticmethod
    def _filter_out_nested_puic_objects(
        df: pd.DataFrame, path_col: str = "path"
    ) -> pd.DataFrame:
        """
        Filter a diff DataFrame to keep only the topmost objects that have a ``@puic``.

        In hierarchical IMX-like data, objects are identified by a ``@puic`` attribute.
        If an object contains a nested object that also has its own ``@puic``, that
        nested subtree is considered independent and should not be included under the
        parent in the filtered view.

        This function:
          1. Identifies all paths ending with ``.@puic``.
          2. Keeps only the *topmost* puic objects (shortest paths not nested under others).
          3. Excludes any rows belonging to nested puic subtrees.
          4. Returns a cleaned DataFrame containing only rows under the topmost puic objects.

        Args:
            df (pd.DataFrame): Input DataFrame with hierarchical paths and ``@puic`` markers.
            path_col (str, optional): Column containing the hierarchical path. Defaults to "path".

        Returns:
            pd.DataFrame: A filtered DataFrame containing only the rows under topmost
                          puic objects, with nested puic subtrees excluded.
        """
        paths = df[path_col].astype(str)

        # Collect all object bases that have a @puic (strip the trailing ".@puic")
        puic_bases = {p.rsplit(".", 1)[0] for p in paths if p.endswith(".@puic")}

        # Keep only topmost puic bases:
        #    - Sort bases by length (shortest first = higher in hierarchy)
        #    - Discard bases that are descendants of already selected bases
        sorted_bases = sorted(puic_bases, key=len)  # shortest first
        topmost_bases: list[str] = []
        for b in sorted_bases:
            if not any(b.startswith(tb + ".") for tb in topmost_bases):
                topmost_bases.append(b)

        # Identify nested puic bases (descendants of a topmost base, not equal to it)
        nested_puic_bases = {
            b
            for b in puic_bases
            if any(b.startswith(tb + ".") for tb in topmost_bases if tb != b)
        }

        # Keep rows:
        #    - that are under a topmost puic base
        #    - but exclude rows under nested puic bases
        def keep_path(p: str) -> bool:
            starts_with_any = any(
                p.startswith(tb + ".") or p == tb for tb in topmost_bases
            )
            under_nested_puic = any(
                p.startswith(nb + ".") or p == nb for nb in nested_puic_bases
            )
            return starts_with_any and not under_nested_puic

        mask = paths.map(keep_path)
        return df[mask].copy()

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
        return self._filter_out_nested_puic_objects(object_specs_df)

    def _build_column_path_map(
        self, df: pd.DataFrame, object_base_path: str
    ) -> pd.DataFrame:
        """
        Construct paths for each DataFrame column relative to a base path.

        Args:
            df (pd.DataFrame): DataFrame with actual data columns.
            object_base_path (str): Path prefix to prepend to columns.

        Returns:
            pd.DataFrame: Mapping of DataFrame columns to normalized spec paths.
        """
        column_path_map_df = pd.DataFrame({"field": df.columns})
        column_path_map_df["path"] = (
            object_base_path + column_path_map_df["field"]
        ).map(self._normalize_path_without_indices)
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
        merged_specs_df["field"] = merged_specs_df["field_y"].fillna(
            merged_specs_df["field_x"]
        )

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
        metadata_header_df = (
            pd.concat([merged_specs_df, direct_match_specs_df])
            .transpose()
            .dropna(how="all")
        )

        return metadata_header_df

    def _merge_metadata_and_data(
        self, df: pd.DataFrame, metadata_header_df: pd.DataFrame
    ) -> pd.DataFrame:
        """
        Merge metadata info into a DataFrame and reorder columns.

        The metadata rows (from `metadata_header_df`) are stacked on top of the
        provided data (`df`) to form a consistent table with aligned columns.

        Args:
            df (pd.DataFrame): The input DataFrame with actual data values.
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
        metadata_label_df = pd.DataFrame(
            {self.metadata_label_col: metadata_header_df.index}
        )
        metadata_label_df = metadata_label_df.set_index(
            metadata_label_df[self.metadata_label_col]
        )

        # Prepend the labels to the metadata header (ensures label column is present)
        metadata_header_df = pd.concat(
            [metadata_label_df, metadata_header_df], axis="columns"
        )

        # Compute the complete set of columns from both metadata and dataframes
        combined_cols = list(set(metadata_header_df.columns) | set(df.columns))

        # Apply the custom sorting logic
        ordered_cols = sorted(combined_cols, key=col_key)

        # Decide final columns:
        # - if dropping "empty" columns, keep only data columns (+ the label column)
        # - else keep everything
        if self.drop_empty_columns:
            data_cols = set(df.columns)
            final_cols = [
                c
                for c in ordered_cols
                if (c in data_cols) or (c == self.metadata_label_col)
            ]
        else:
            final_cols = ordered_cols

        # Reindex to ensure both frames have the same columns, in the same order
        metadata_header_df = metadata_header_df.reindex(columns=final_cols)
        df = df.reindex(columns=final_cols)

        # Prepare an empty dataframe to enforce column ordering
        empty_ordering_df = pd.DataFrame(columns=final_cols)

        # Concat ensures consistent columns + merges metadata & dataframes
        contacted_df = pd.concat([empty_ordering_df, metadata_header_df, df], axis=0)

        return contacted_df

    def apply_metadata_header(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Annotate a DataFrame with specification metadata.

        Prepends one or more metadata rows (from the spec CSV) above the actual
        data rows, ensuring consistent column ordering. The result is ready to
        export directly to Excel with self-documenting headers.

        Args:
            df: Input DataFrame. Must contain a 'path_to_root' column.

        Returns:
            DataFrame with metadata rows stacked on top of the original data rows.
        """
        original_order = df.columns.tolist()
        object_base_path = self._clean_path(df["path_to_root"].values[0]) + "."
        object_specs_df = self._get_specs_for_object(object_base_path=object_base_path)
        column_path_map_df = self._build_column_path_map(
            df=df, object_base_path=object_base_path
        )
        metadata_header_df = self._build_metadata_header(
            object_specs_df=object_specs_df, column_path_map_df=column_path_map_df
        )

        df_with_header = self._merge_metadata_and_data(
            df=df, metadata_header_df=metadata_header_df
        )
        del df_with_header["path_to_root"]

        original_order.insert(0, "IndexInfo")
        original_order.remove("path_to_root")
        df_with_header = df_with_header[original_order]
        return df_with_header

    @staticmethod
    def to_excel_with_metadata(
        writer,
        sheet_name: str,
        df: pd.DataFrame,
        *,
        index: bool = False,
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
            index (bool, optional): Write index column. Default False.
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
            index=index,
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
            index=index,
            header=header,
            startrow=metadata_rows,
        )

        worksheet.freeze_panes(metadata_rows + 1, 2)

        # Calculate widths and apply filter only to the data area
        data_df = df.data if isinstance(df, Styler) else df  # type: ignore

        if auto_filter and not data_df.empty:
            apply_autofilter(worksheet, start_row=metadata_rows, data_df=data_df)

        # TODO: refactor below
        autosize_columns(
            worksheet=worksheet,
            full_df=df,
            data_start_row=metadata_rows,
            min_width=15,
            header_min_width=80,
            padding=2,
        )
        worksheet.set_column("A:A", options={"level": 1, "hidden": True})
        worksheet.set_column("H:I", options={"level": 1, "hidden": True})

        return worksheet


@dataclass
class HeaderSpec:
    """
    Dataclass wrapper for header specification files.

    !!! danger "Experimental feature"
        HeaderSpec is considered experimental and WILL change without warning.

    Encapsulates configuration for creating a HeaderAnnotator. Use this
    class when you want to bundle spec file location and options together.

    Attributes:
        spec_csv_path: Path to the CSV file with header metadata.
        spec_path_col: Column in the spec that defines canonical paths. Default "path".
        spec_ignore_cols: List of spec fields to ignore when loading.
        drop_empty_columns: If True, drop columns that are empty after merging.

    Methods:
        get_annotator(): Create a HeaderAnnotator configured with this spec.

    ## Specification CSV

    The specification CSV provides **metadata for DataFrame columns** that are exported
    to Excel (diff and population report). It defines a metadata block whit info about the columns.

    ### File structure

    The CSV must contain at least one column:

    - **path** (*required*): A canonical field path this row describes.
      - Written in dot notation, without numeric indices.
      - Examples:
        - ``SingleSwitch.@puic`` or ``SingleSwitch.extension.MicroNode.@railConnectionRef``.

    Other columns will be rendered as **documentation rows** above the table header.

    Example metadata columns include:

    - **description**: Explanation of the field’s meaning.
    - **datatype**: Expected type (e.g. ``string``, ``number``, ``enum:…``).
    - **required**: Whether the field is mandatory (``yes``/``no``).
    - **domain**: Controlled vocabulary or external reference.

    #### Example

    ```csv
    path,label,description,datatype,required,documentation,documentation_link
    SingleSwitch.@puic,PUIC,Unique object identifier,string,yes,PUIC spec,https://docs.example/puic
    SingleSwitch.parent,Parent PUIC,Parent object reference,string,no,Parent ref,https://docs.example/parent
    SingleSwitch.extension.MicroNode.@railConnectionRef,RailConn Ref,Reference to rail connection,string,no,Ext ref,https://docs.example/railconn
    ```

    ### Hyperlink support

    If a column ``X`` has a companion ``X_link`` column, the loader will replace ``X`` with an Excel
    HYPERLINK formula pointing to ``X_link``.

    Example:

    - ``documentation`` + ``documentation_link`` →
      ``=HYPERLINK("https://docs.example/puic", "PUIC spec")``

    ### Excel export
    The world runs on Excel so we generate an Excel sheet where metadata rows are
    stacked above the data rows, making the report self-documenting.

    """

    spec_csv_path: str
    drop_empty_columns: bool = False
    spec_path_col: str = "path"
    spec_ignore_cols: list[str] = field(default_factory=list)

    def get_annotator(self) -> "HeaderAnnotator":
        """Return a `HeaderAnnotator` configured with this spec."""
        return HeaderAnnotator(
            self.spec_csv_path,
            self.spec_path_col,
            self.drop_empty_columns,
            spec_ignore_cols=self.spec_ignore_cols,
        )
