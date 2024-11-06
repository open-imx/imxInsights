import pandas as pd
from pandas import DataFrame, Series

from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
from imxInsights.utils.flatten_unflatten import hash_sha256


class ContainerImxPandasGenerator:
    def __init__(self, container: ImxContainerProtocol) -> None:
        self._container = container

    def _create_metadata_df(
        self, metadata: dict[str, str | None], metadata_type: str
    ) -> DataFrame:
        """Helper method to create a DataFrame from metadata."""
        df: DataFrame = pd.DataFrame(list(metadata.items()), columns=["Key", "Value"])
        df["Type"] = metadata_type
        df["Key_1"] = df["Key"]
        df["Key_2"] = ""  # No specific suffix for keys
        return df

    def imx_info_df(self) -> DataFrame:
        """Generate DataFrame containing general IMX info."""
        imx_info: dict[str, str | None] = {
            "container_id": self._container.container_id,
            "file_path": f"{self._container.path}",
            "calculated_file_hash": hash_sha256(self._container.path),
            "imx_version": self._container.files.signaling_design.imx_version
            if self._container.files.signaling_design
            else None,
        }
        return self._create_metadata_df(imx_info, "General Info")

    def project_metadata_df(self) -> DataFrame:
        """Get project metadata as a DataFrame."""
        if self._container.project_metadata is None:
            return DataFrame()

        metadata = self._container.project_metadata
        metadata_info: dict[str, str | None] = {
            "project_name": metadata.project_name or "NONE",
            "external_project_reference": metadata.external_project_reference or "NONE",
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
        return self._create_metadata_df(metadata_info, "Imx Metadata")

    def _generate_file_data(self) -> list[tuple[str, str | None, str, str]]:
        """Helper method to gather file information for DataFrame."""
        file_data: list[tuple[str, str | None, str, str]] = []
        for file in self._container.files:
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

        return file_data

    def files_info_df(self) -> DataFrame:
        """Generate DataFrame containing file information."""
        file_data = self._generate_file_data()
        df_files: DataFrame = pd.DataFrame(
            file_data, columns=["Key", "Value", "Key_1", "Key_2"]
        )
        df_files["Type"] = "Files Info"
        return df_files

    def build_errors_df(self) -> DataFrame:
        """Generate DataFrame containing build errors."""
        error_data: list[tuple[str, str, str, str]] = []
        build_exceptions = self._container.get_build_exceptions()
        for key, value in build_exceptions.items():
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
        df_errors["Key"] = df_errors.groupby(["Key_1", "Key_2"]).cumcount() + 1

        # todo: build errors are not pivoting course of duplicated indexes
        # df_errors[['Key_2', 'Value']] = df_errors[['Value', 'Key_2']]
        df_errors[["Type", "Key", "Key_1", "Key_2"]] = df_errors[
            ["Key_2", "Value", "Key_1", "Key"]
        ]

        df_merged: DataFrame = pd.concat(
            [df_imx_info, self.project_metadata_df(), df_files, df_errors],
            ignore_index=True,
            sort=False,
        )
        type_order: list[str] = [
            "General Info",
            "Project Metadata",
            "Files Info",
            "ERROR",
            "WARNING",
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

        return df_merged.drop(columns=["Key"])
