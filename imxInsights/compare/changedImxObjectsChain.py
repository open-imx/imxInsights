from pathlib import Path

import pandas as pd

from imxInsights.utils.excel_helpers import clean_diff_df, shorten_sheet_name
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    style_puic_groups,
    styler_highlight_changes,
)


class ChangedImxObjectsChain:
    def __init__(
        self,
        imx_repo,
        container_id_pairs: list[tuple[str, str]],
        object_path: list[str] | None = None,
        container_id_name_mapping: dict[str, str] | None = None,
    ):
        self.imx_repo = imx_repo
        self.container_id_pairs = container_id_pairs
        self.object_path = object_path
        self.container_id_name_mapping = container_id_name_mapping

        self._validate_inputs()
        self.data = self._perform_comparisons()

    def _validate_inputs(self):
        """Ensure the input mappings align with the given container IDs."""
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

    def _perform_comparisons(self) -> list[dict]:
        """Perform comparisons across container pairs and return formatted data."""
        data = []

        for idx, (container_id_a, container_id_b) in enumerate(self.container_id_pairs):
            snapshot_name = {"snapshot_name": ""}
            if self.container_id_name_mapping:
                snapshot_name["snapshot_name"] = (
                    f"{self.container_id_name_mapping[container_id_a]} vs {self.container_id_name_mapping[container_id_b]}"
                )

            compared_objects = self.imx_repo.compare(
                container_id_a, container_id_b, self.object_path
            ).compared_objects

            data.extend(
                [
                    item.get_change_dict()
                    | snapshot_name
                    | {
                        "snapshot": idx,
                        "container_id_1": container_id_a,
                        "container_id_2": container_id_b,
                    }
                    for item in compared_objects
                ]
            )

        return data

    def get_dataframe(self) -> pd.DataFrame:
        """Generate a styled Pandas DataFrame from comparison results."""
        df = pd.DataFrame(self.data)
        if df.empty:
            return df

        df = clean_diff_df(df)

        puic_values = df["@puic"].unique()
        snapshot_values = df["snapshot"].unique()
        all_combinations = pd.MultiIndex.from_product(
            [puic_values, snapshot_values], names=["@puic", "snapshot"]
        ).to_frame(index=False)
        df = all_combinations.merge(df, on=["@puic", "snapshot"], how="left")

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

        return df.style.map(styler_highlight_changes).apply(  # type: ignore[attr-defined]
            style_puic_groups, axis=None
        )

    def to_excel(self, file_path: str | Path):
        """Writes the comparison results to an Excel file, applying formatting."""
        file_path = Path(file_path).resolve()

        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            paths = self.imx_repo.get_all_paths()

            for path in sorted(paths):
                sheet_name = shorten_sheet_name(path)

                compare = ChangedImxObjectsChain(
                    self.imx_repo,
                    self.container_id_pairs,
                    object_path=[path],
                    container_id_name_mapping=self.container_id_name_mapping,
                )

                styler_df = compare.get_dataframe()
                if styler_df.data.empty:
                    continue

                styler_df.to_excel(writer, sheet_name=sheet_name, index=False)
                worksheet = writer.sheets[sheet_name]
                worksheet.autofit()
                worksheet.freeze_panes(1, 0)
