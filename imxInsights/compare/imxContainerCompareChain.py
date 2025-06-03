from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.compare.imxContainerCompare import ImxContainerCompare
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    style_puic_groups,
    styler_highlight_changes,
)
from imxInsights.utils.report_helpers import (
    clean_diff_df,
    shorten_sheet_name,
    upper_keys_with_index,
)


class ImxContainerCompareChain:
    # todo: conceptual this shares code whit normal compare, check what can moved in separated methods

    def __init__(
        self,
        imx_repo,
        container_id_pairs: list[tuple[str, str]],
        container_id_name_mapping: dict[str, str] | None = None,
    ):
        """
        Initializes the comparison chain for the given container ID pairs.

        Args:
            imx_repo: The IMX repository object that holds the container data.
            container_id_pairs: A list of tuples containing pairs of container IDs to compare.
            container_id_name_mapping: An optional dictionary mapping container IDs to names.

        Raises:
            ValueError: If any container ID in the pairs is not found in the repository.
        """

        self.imx_repo = imx_repo
        self.container_id_pairs = container_id_pairs
        self.container_id_name_mapping = container_id_name_mapping
        self._validate_inputs()
        self._compare: list[ImxContainerCompare] = []
        self._set_comparisons()

    def _validate_inputs(self):
        if not all(
            item in self.imx_repo.container_order
            for pair in self.container_id_pairs
            for item in pair
        ):
            raise ValueError("container_id not in multi repo")
        if self.container_id_name_mapping:
            container_id_keys = {
                cid for pair in self.container_id_pairs for cid in pair
            }
            if not all(
                key in container_id_keys
                for key in self.container_id_name_mapping.keys()
            ):
                raise ValueError(
                    "container_id_name_mapping not matching the given container_ids"
                )

    def _set_comparisons(self) -> None:
        for idx, (container_id_a, container_id_b) in enumerate(self.container_id_pairs):
            compare = self.imx_repo.compare(container_id_a, container_id_b)
            self._compare.append(compare)

    def _get_combined_dataframe(self, object_paths: list[str]):
        dfs = []
        for idx, item in enumerate(self._compare):
            df = item.get_pandas(object_paths=object_paths, styled_df=False)
            if df.empty:
                continue

            if self.container_id_name_mapping:
                df["snapshot_name"] = (
                    f"{self.container_id_name_mapping[item.container_id_1]} vs {self.container_id_name_mapping[item.container_id_2]}"
                )
            df["snapshot"] = idx
            df["container_id_1"] = item.container_id_1
            df["container_id_2"] = item.container_id_2
            df = clean_diff_df(df)
            dfs.append(df)
        if len(dfs) == 0:
            return pd.DataFrame()
        return pd.concat(dfs, ignore_index=True)

    @staticmethod
    def _process_dataframe(df: pd.DataFrame):
        puic_values = df["@puic"].unique()
        snapshot_values = df["snapshot"].unique()
        all_combinations = pd.MultiIndex.from_product(
            [puic_values.tolist(), snapshot_values.tolist()],
            names=["@puic", "snapshot"],
        ).to_frame(index=False)
        df = all_combinations.merge(df, on=["@puic", "snapshot"], how="left")

        for col in df.select_dtypes(include="category").columns:
            df[col] = df[col].cat.add_categories("").fillna("")
        df = df.fillna("")

        start_column = [
            "container_id_1",
            "container_id_2",
            "snapshot",
            "snapshot_name",
            "parent",
            "children",
            "tag",
            "path",
            "@puic",
            "status",
            "geometry_status",
            "@name",
        ]
        end_columns = [col for col in df.columns if "extension" in col]
        df = df_columns_sort_start_end(df, start_column, end_columns)

        custom_order = ["added", "changed", "unchanged", "type_change", "removed"]
        df["status"] = pd.Categorical(
            df["status"], categories=custom_order, ordered=True
        )
        return df

    @staticmethod
    def _style_dataframe(df):
        # TODO: move to report helpers, make sure te reuse else in the code
        return df.style.map(styler_highlight_changes).apply(  # type: ignore[attr-defined]
            style_puic_groups, axis=None
        )

    def get_dataframe(
        self,
        object_paths: list[str],
        styled_df: bool = True,
    ) -> pd.DataFrame:
        """
        Retrieves a processed dataframe for the given object paths.

        Args:
            object_paths: A list of object paths to retrieve data from.
            styled_df: Whether to apply styling to the dataframe. Defaults to True.

        Returns:
            pd.DataFrame: The processed and optionally styled dataframe with comparison results,
                optionally styled as pd.Styler.
        """
        df = self._get_combined_dataframe(object_paths)
        if df.empty:
            return df

        df = self._process_dataframe(df)

        if styled_df:
            df = self._style_dataframe(df)
        return df

    def get_overview_dataframe(
        self,
        styled_df: bool = True,
    ):
        """
        Retrieves an overview dataframe for the comparison results.

        Args:
            styled_df: Whether to apply styling to the dataframe. Defaults to True.

        Returns:
            pd.DataFrame: The overview dataframe, optionally styled as pd.Styler.
        """
        df = self.get_dataframe(
            object_paths=self.imx_repo.get_all_paths(), styled_df=False
        )
        columns_to_keep = [
            "container_id_1",
            "container_id_2",
            "snapshot",
            "snapshot_name",
            "parent",
            "children",
            "@puic",
            "tag",
            "path",
            "@name",
            "Location.GeographicLocation.@accuracy",
            "Location.GeographicLocation.@dataAcquisitionMethod",
            "Metadata.@isInService",
            "Metadata.@lifeCycleStatus",
            "Metadata.@source",
        ]
        df = df[df.columns.intersection(columns_to_keep)]
        if styled_df:
            return self._style_dataframe(df)
        return df

    def to_excel(self, file_path: str | Path):
        """
        Writes the comparison results to an Excel file, applying formatting.

        Args:
            file_path: The path to save the Excel file.

        """

        file_path = Path(file_path).resolve()

        paths = self.imx_repo.get_all_paths()
        diff_dict = {path: self.get_dataframe([path]) for path in sorted(paths)}
        diff_dict = upper_keys_with_index(diff_dict)

        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            for path, df in diff_dict.items():
                logger.info(f"create sheet for imx path {path}")
                sheet_name = shorten_sheet_name(path)

                df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                worksheet.autofit()
                worksheet.freeze_panes(1, 0)

                num_cols = len(df.columns)
                worksheet.autofilter(0, 0, 0, num_cols)
