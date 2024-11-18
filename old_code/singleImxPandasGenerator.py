import pandas as pd
from pandas import DataFrame

from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol
from imxInsights.utils.hash import hash_sha256


class SingleImxPandasGenerator:
    def __init__(self, situation: ImxSituationProtocol):
        self._situation = situation

    @staticmethod
    def _generate_df(info_dict: dict, info_type: str, suffix: str = "") -> DataFrame:
        """Creates a DataFrame from a dictionary with additional type and suffix information."""
        return pd.DataFrame(
            [
                {"Key": k, "Value": v, "Type": info_type, "Key_1": k, "Key_2": suffix}
                for k, v in info_dict.items()
            ]
        )

    def _get_general_info(self) -> dict:
        """Generates general IMX info dictionary."""
        return {
            "container_id": self._situation.container_id,
            "file_path": self._situation._imx_file.absolute_path,
            "calculated_file_hash": hash_sha256(self._situation._imx_file.path),
            "imx_version": self._situation.imx_version,
        }

    def _get_project_metadata(self) -> dict:
        """Returns project metadata if available, otherwise returns an empty dictionary."""
        metadata = self._situation.project_metadata
        if metadata is None:
            return {}

        return {
            "project_name": metadata.project_name,
            "external_project_reference": metadata.external_project_reference,
            "created_date": metadata.created_date.isoformat()
            if metadata.created_date
            else "NONE",
            "planned_delivery_date": metadata.planned_delivery_date.isoformat()
            if metadata.planned_delivery_date
            else "NONE",
        }

    def _get_situation_info(self) -> dict:
        """Generates situation info dictionary."""
        return {
            "situation_type": self._situation.situation_type.name,
            "perspective_date": self._situation.perspective_date.isoformat()
            if self._situation.perspective_date
            else "NONE",
            "reference_date": self._situation.reference_date.isoformat()
            if self._situation.reference_date
            else "NONE",
        }

    def _get_build_errors(self) -> list[tuple[str, str, str, str]]:
        """Generates a list of build errors."""
        build_exceptions = self._situation.get_build_exceptions()
        return [
            (f"{item.msg}", f"{item.msg}", key, item.level.name)
            for key, value in build_exceptions.items()
            for item in value
        ]

    def imx_info_df(self) -> DataFrame:
        """Generate DataFrame containing general IMX info."""
        return self._generate_df(self._get_general_info(), "General Info")

    def project_metadata_df(self) -> DataFrame:
        """Generate DataFrame containing project metadata."""
        return self._generate_df(self._get_project_metadata(), "Imx Metadata")

    def situation_info_df(self) -> DataFrame:
        """Generate DataFrame containing situation info."""
        return self._generate_df(self._get_situation_info(), "Situation Info")

    def build_errors_df(self) -> DataFrame:
        """Generate DataFrame containing build errors."""
        error_data = self._get_build_errors()
        df_errors = pd.DataFrame(error_data, columns=["Key", "Value", "Key_1", "Key_2"])
        df_errors["Type"] = "Build Errors"
        return df_errors

    def combined_info_df(
        self, include_build_errors: bool = True, pivot_df: bool = True
    ) -> DataFrame:
        """Generates a combined DataFrame with all info, optionally including build errors and pivoted view."""
        data_frames = [
            self.imx_info_df(),
            self.project_metadata_df(),
            self.situation_info_df(),
        ]

        if include_build_errors:
            data_frames.append(self.build_errors_df())

        combined_df = pd.concat(data_frames, ignore_index=True, sort=False)
        type_order = ["General Info", "Imx Metadata", "Situation Info", "Build Errors"]
        combined_df["Type"] = pd.Categorical(
            combined_df["Type"], categories=type_order, ordered=True
        )

        if pivot_df:
            return (
                combined_df.groupby(
                    ["Type", "Key_1", "Key_2"], as_index=False, observed=True
                )["Value"]
                .first()
                .set_index(["Type", "Key_1", "Key_2"])
            )

        combined_df.drop(columns=["Key"], inplace=True)
        combined_df.insert(len(combined_df.columns), "name", combined_df.pop("Value"))
        return combined_df
