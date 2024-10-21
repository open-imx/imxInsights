from pathlib import Path

import pandas as pd
from pandas import DataFrame, Series

from imxInsights.file.containerizedImx.imxContainerFiles import ImxContainerFiles
from imxInsights.file.containerizedImx.imxContainerMetadata import ImxContainerMetadata
from imxInsights.repo.tree.buildExceptions import BuildExceptions
from imxInsights.utils.flatten_unflatten import hash_sha256


class ContainerImxPandasGenerator:
    def __init__(
        self,
        container_id: str,
        input_file_path: Path,
        files: ImxContainerFiles,
        project_metadata: ImxContainerMetadata | None,
        build_exceptions: BuildExceptions,
    ) -> None:
        self._container_id: str = container_id
        self._input_file_path: Path = input_file_path
        self._files: ImxContainerFiles = files
        self._project_metadata: ImxContainerMetadata | None = project_metadata
        self._build_exceptions: BuildExceptions = build_exceptions

    def imx_info_df(self) -> DataFrame:
        """Generate DataFrame containing general IMX info."""
        imx_info: dict[str, str | Path | None] = {
            "container_id": self._container_id,
            "file_path": self._input_file_path,
            "calculated_file_hash": hash_sha256(self._input_file_path),
            "imx_version": self._files.signaling_design.imx_version
            if self._files.signaling_design
            else None,
        }
        df_imx_info: DataFrame = pd.DataFrame(
            list(imx_info.items()), columns=["Key", "Value"]
        )
        df_imx_info["Type"] = "General Info"
        df_imx_info["Key_1"] = df_imx_info["Key"]
        df_imx_info["Key_2"] = ""  # No specific suffix for general info keys
        return df_imx_info

    def project_metadata_df(self) -> DataFrame:
        """Get project metadata as a DataFrame."""
        if self._project_metadata is None:
            return DataFrame()

        metadata = self._project_metadata

        metadata_info: dict[str, str | None] = {
            "project_name": metadata.project_name if metadata.project_name else "NONE",
            "external_project_reference": metadata.external_project_reference
            if metadata.external_project_reference
            else "NONE",
            "exchange_phase": metadata.data_exchange_phase.value
            if metadata.data_exchange_phase
            else "NONE",
            "created_date": metadata.created_date.isoformat()
            if metadata.created_date
            else "NONE",
            "planned_delivery_date": metadata.planned_delivery_date.isoformat()
            if metadata.planned_delivery_date
            else "NONE",
        }

        metadata_df: DataFrame = pd.DataFrame(
            list(metadata_info.items()), columns=["Key", "Value"]
        )
        metadata_df["Type"] = "Imx Metadata"
        metadata_df["Key_1"] = metadata_df["Key"]
        metadata_df["Key_2"] = ""  # No specific suffix for general info keys
        return metadata_df

    def files_info_df(self) -> DataFrame:
        """Generate DataFrame containing file information."""
        file_data: list[tuple[str, str | None, str, str]] = []
        for file in self._files:
            if file is not None:
                file_data.append(
                    (f"{file.path.name}_hash", file.file_hash, file.path.name, "hash")
                )
                file_data.append(
                    (
                        f"{file.path.name}_hash_calculated",
                        hash_sha256(file.path),
                        file.path.name,
                        "hash_calculated",
                    )
                )

                if hasattr(file, "base_reference"):
                    file_data.append(
                        (
                            f"{file.path.name}_base reference file",
                            file.base_reference.parent_document_name,
                            file.path.name,
                            "base reference file",
                        )
                    )
                    file_data.append(
                        (
                            f"{file.path.name}_base reference hash",
                            file.base_reference.parent_hashcode,
                            file.path.name,
                            "base reference hash",
                        )
                    )

        df_files: DataFrame = pd.DataFrame(
            file_data, columns=["Key", "Value", "Key_1", "Key_2"]
        )
        df_files["Type"] = "Files Info"  # Add a type column for classification
        return df_files

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
        self, files: bool = True, build_errors: bool = True, pivot_df: bool = True
    ) -> DataFrame | Series:
        """Generate a comprehensive DataFrame with IMX, files, and build error information."""
        df_imx_info: DataFrame = self.imx_info_df()
        df_files: DataFrame = (
            self.files_info_df()
            if files
            else pd.DataFrame(columns=["Key", "Value", "Key_1", "Key_2", "Type"])
        )
        df_errors: DataFrame = (
            self.build_errors_df()
            if build_errors
            else pd.DataFrame(columns=["Key", "Value", "Key_1", "Key_2", "Type"])
        )

        # Create output DataFrame
        df_merged: DataFrame = pd.concat(
            [df_imx_info, self.project_metadata_df(), df_files, df_errors],
            ignore_index=True,
            sort=False,
        )
        type_order: list[str] = [
            "General Info",
            "Project Metadata",
            "Files Info",
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
        return df_merged
