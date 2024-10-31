from pathlib import Path

import pandas as pd
from pandas import DataFrame

from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol
from imxInsights.utils.flatten_unflatten import hash_sha256


class SingleImxPandasGenerator:
    def __init__(self, situation: ImxSituationProtocol):
        self._situation = situation

    @staticmethod
    def _generate_df_from_dict(
        info_dict: dict, info_type: str, suffix: str = ""
    ) -> DataFrame:
        """Helper method to generate DataFrame from a dictionary."""
        return pd.DataFrame(
            [
                {"Key": k, "Value": v, "Type": info_type, "Key_1": k, "Key_2": suffix}
                for k, v in info_dict.items()
            ]
        )

    def imx_info_df(self) -> DataFrame:
        """Generate DataFrame containing general IMX info."""
        imx_info = {
            "container_id": self._situation.container_id,
            "file_path": self._situation._imx_file.absolute_path,
            "calculated_file_hash": hash_sha256(self._situation._imx_file.path),
            "imx_version": self._situation.imx_version,
        }
        return self._generate_df_from_dict(imx_info, "General Info")

    def project_metadata_df(self) -> DataFrame:
        """Get project metadata as a DataFrame."""
        if self._situation.project_metadata is None:
            return DataFrame()

        metadata = self._situation.project_metadata
        metadata_info = {
            "project_name": metadata.project_name,
            "external_project_reference": metadata.external_project_reference,
            "created_date": metadata.created_date.isoformat()
            if metadata.created_date
            else "NONE",
            "planned_delivery_date": metadata.planned_delivery_date.isoformat()
            if metadata.planned_delivery_date
            else "NONE",
        }
        return self._generate_df_from_dict(metadata_info, "Imx Metadata")

    def situation_info(self) -> DataFrame:
        """Generate DataFrame for situation info."""
        situation_info: dict[str, str | Path | None] = {
            "situation_type": self._situation.situation_type.name,
            "perspective_date": self._situation.perspective_date.isoformat()
            if self._situation.perspective_date
            else "NONE",
            "reference_date": self._situation.reference_date.isoformat()
            if self._situation.reference_date
            else "NONE",
        }
        return self._generate_df_from_dict(situation_info, "Situation Info")

    def build_errors_df(self) -> DataFrame:
        """Generate DataFrame containing build errors."""
        error_data: list[tuple[str, str, str, str]] = []
        build_exceptions = self._situation.get_build_exceptions()
        for key, value in build_exceptions.items():
            for item in value:
                error_data.append((f"{item.msg}", f"{item.msg}", key, item.level.name))

        df_errors: DataFrame = pd.DataFrame(
            error_data, columns=["Key", "Value", "Key_1", "Key_2"]
        )
        df_errors["Type"] = "Build Errors"
        return df_errors

    def combined_info_df(
        self, build_errors: bool = True, pivot_df: bool = True
    ) -> DataFrame:
        df_imx_info: DataFrame = self.imx_info_df()
        df_metadata: DataFrame = self.project_metadata_df()
        df_situation: DataFrame = self.situation_info()
        df_build_errors: DataFrame = (
            self.build_errors_df()
            if build_errors
            else pd.DataFrame(columns=["Key", "Value", "Key_1", "Key_2", "Type"])
        )

        df_merged: DataFrame = pd.concat(
            [df_imx_info, df_metadata, df_situation, df_build_errors],
            ignore_index=True,
            sort=False,
        )
        type_order: list[str] = [
            "General Info",
            "Imx Metadata",
            "Situation Info",
            "Build Errors",
        ]
        df_merged["Type"] = pd.Categorical(
            df_merged["Type"], categories=type_order, ordered=True
        )

        if pivot_df:
            pivot: DataFrame = df_merged.groupby(
                ["Type", "Key", "Key_1", "Key_2"], as_index=False, observed=True
            ).agg({"Value": "first"})
            pivot = pivot.drop(columns=["Key"])
            pivot.set_index(["Type", "Key_1", "Key_2"], inplace=True)
            return pivot

        df_merged = df_merged.drop(columns=["Key"])
        column_to_move = df_merged.pop("Value")
        df_merged.insert(len(df_merged.columns), "name", column_to_move)
        return df_merged
