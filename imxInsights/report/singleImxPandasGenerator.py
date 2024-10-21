from pathlib import Path

import pandas as pd
from pandas import DataFrame
from pydantic.schema import datetime

from imxInsights.file.imxFile import ImxFile
from imxInsights.file.singleFileImx.imxSingleFileMetadata import SingleImxMetadata
from imxInsights.file.singleFileImx.imxSituationEnum import ImxSituationEnum
from imxInsights.repo.tree.buildExceptions import BuildExceptions
from imxInsights.utils.flatten_unflatten import hash_sha256


class SingleImxPandasGenerator:
    def __init__(
        self,
        container_id: str,
        input_file_path: Path,
        imx_file: ImxFile,
        project_metadata: SingleImxMetadata | None,
        build_exceptions: BuildExceptions,
        situation: ImxSituationEnum,
        reference_date: datetime | None,
        perspective_date: datetime | None,
    ):
        self._container_id = container_id
        self._input_file_path = input_file_path
        self._imx_file = imx_file
        self._project_metadata = project_metadata
        self._build_exceptions = build_exceptions
        self._situation = situation
        self._reference_date = reference_date
        self._perspective_date = perspective_date

    def _generate_df_from_dict(
        self, info_dict: dict, info_type: str, suffix: str = ""
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
            "container_id": self._container_id,
            "file_path": self._input_file_path,
            "calculated_file_hash": hash_sha256(self._input_file_path),
            "imx_version": self._imx_file.imx_version,
        }
        return self._generate_df_from_dict(imx_info, "General Info")

    def project_metadata_df(self) -> DataFrame:
        """Get project metadata as a DataFrame."""
        if self._project_metadata is None:
            return DataFrame()

        metadata = self._project_metadata
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
            "situation_type": self._situation.name,
            "perspective_date": self._perspective_date.isoformat()
            if self._perspective_date
            else "NONE",
            "reference_date": self._reference_date.isoformat()
            if self._reference_date
            else "NONE",
        }
        return self._generate_df_from_dict(situation_info, "Situation Info")

    def build_errors_df(self) -> DataFrame:
        """Generate DataFrame containing build errors."""
        error_data: list[tuple[str, str, str, str]] = []
        for key, value in self._build_exceptions.exceptions.items():
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
