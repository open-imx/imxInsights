from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    styler_highlight_changes,
)
from imxInsights.utils.report_helpers import (
    clean_diff_df,
    lower_and_index_duplicates,
    shorten_sheet_name,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)


class ChangedImxObjects:
    """
    Represents a collection of compared ImxObject instances, providing
    functionality to extract differences, generate GeoJSON files,
    and export data to Excel.
    """

    def __init__(self, compared_objects: list[ChangedImxObject]):
        """
        Initializes a new ChangedImxObjects instance.

        Args:
            compared_objects: A list of ChangedImxObject instances representing the compared objects.
        """
        self.compared_objects: list[ChangedImxObject] = compared_objects

    def get_geojson(
        self,
        object_paths: list[str] | None = None,
        to_wgs: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        """
        Generates a GeoJSON feature collection representing the changed objects.

        Args:
            object_paths:: An optional list of object paths to filter the GeoJSON features. If None, all changed objects are included.
            to_wgs: A boolean indicating whether to convert the coordinates to WGS84.

        Returns:
            A ShapelyGeoJsonFeatureCollection representing the changed objects.
        """
        if object_paths:
            features = self._get_features_by_path(object_paths, to_wgs=to_wgs)
        else:
            features = [
                item.as_geojson_feature(as_wgs=to_wgs) for item in self.compared_objects
            ]

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def _get_features_by_path(
        self,
        object_paths: list[str],
        to_wgs: bool = True,
    ) -> list[ShapelyGeoJsonFeature]:
        """
        Helper function to get GeoJSON features by object path.

        Args:
            object_paths: A list of object paths to filter the GeoJSON features.
            to_wgs: A boolean indicating whether to convert the coordinates to WGS84.

        Returns:
            A list of ShapelyGeoJsonFeature objects.
        """
        features = []
        for item in self.compared_objects:
            if item.t1 and item.t1.path in object_paths:
                features.append(item.as_geojson_feature(as_wgs=to_wgs))
            if item.t2 and item.t2.path in object_paths:
                features.append(item.as_geojson_feature(as_wgs=to_wgs))
        return features

    def create_geojson_files(
        self, directory_path: str | Path, to_wgs: bool = True
    ) -> None:
        """
        Creates GeoJSON files for each unique object path in the compared objects.

        Args:
            directory_path: The path to the directory where the GeoJSON files will be created.
            to_wgs: A boolean indicating whether to convert the coordinates to WGS84.
        """
        if isinstance(directory_path, str):
            directory_path = Path(directory_path)

        directory_path.mkdir(parents=True, exist_ok=True)

        paths = self.get_all_paths()
        paths = lower_and_index_duplicates(paths)

        for path in paths:
            file_name = f"{directory_path}\\{path}.geojson"
            geojson_collection = self.get_geojson([path], to_wgs)
            geojson_collection.to_geojson_file(file_name)

    def get_overview_df(self) -> pd.DataFrame:
        """
        Generates an overview DataFrame summarizing the changes between the objects.

        Returns:
            A pandas DataFrame representing the overview of changes.
        """
        out = [item.get_change_dict() for item in self.compared_objects]
        df = pd.DataFrame(out)
        if not df.empty:
            df = clean_diff_df(df)

        columns_to_keep = [
            "@puic",
            "path",
            "parent",
            "status",
            "Metadata.@isInService",
            "Metadata.@lifeCycleStatus",
            "Metadata.@originType",
            "Metadata.@source",
        ]

        # Reindex the DataFrame to ensure the desired column order and fill missing columns
        df = df.reindex(columns=columns_to_keep, fill_value="")

        df = df.style.map(styler_highlight_changes)  # type: ignore[attr-defined]
        return df

    def get_all_paths(self) -> set[str]:
        """
        Returns a sorted list of all unique object paths in the compared objects.

        Returns:
            A sorted list of unique object paths.
        """
        return set(
            sorted(
                list(
                    [
                        obj.path
                        for item in self.compared_objects
                        for obj in (item.t1, item.t2)
                        if obj
                    ]
                )
            )
        )

    def get_pandas(
        self, object_paths: list[str], add_analyse: bool = False, styled_df: bool = True
    ) -> pd.DataFrame:
        """
        Generates a DataFrame detailing the changes for a specific object path.

        Args:
            object_paths: A list containing the object path to filter the changes.
            add_analyse: Add analyse to dataframe
            styled_df: Style changes in dataframe

        Returns:
            A pandas DataFrame representing the changes for the specified object path.
        """
        items = [
            item
            for item in self.compared_objects
            if (item.t1 and item.t1.path in object_paths)
            or (item.t2 and item.t2.path in object_paths)
        ]

        out = [item.get_change_dict(add_analyse=add_analyse) for item in items]

        df = pd.DataFrame(out)
        if not df.empty:
            df = clean_diff_df(df)

            df = df_columns_sort_start_end(
                df,
                [
                    "@puic",
                    "path",
                    "tag",
                    "parent",
                    "children",
                    "status",
                    "geometry_status",
                    "@name",
                ],
                [],
            )
            df = df.fillna("")

            status_order = ["added", "changed", "unchanged", "type_change", "removed"]
            df["status"] = pd.Categorical(
                df["status"], categories=status_order, ordered=True
            )
            df = df.sort_values(by=["path", "status"])
            if styled_df:
                df = df.style.map(styler_highlight_changes)  # type: ignore[attr-defined]

        return df

    def to_excel(
        self, file_name: str | Path, add_analyse: bool = False, styled_df: bool = True
    ) -> None:
        """
        Exports the overview and detailed changes to an Excel file.

        Args:
            file_name: The name or path of the Excel file to create.
            add_analyse: Add analyse to excel
            styled_df: Style changes in excel
        """
        file_name = Path(file_name) if isinstance(file_name, str) else file_name

        paths = self.get_all_paths()

        logger.info("create change excel file")

        diff_dict = {
            item: self.get_pandas([item], add_analyse=add_analyse, styled_df=styled_df)
            for item in paths
        }
        with pd.ExcelWriter(file_name, engine="xlsxwriter") as writer:
            try:
                logger.debug("creating overview")
                overview_df = self.get_overview_df()
                overview_df.to_excel(writer, sheet_name="overview")
                worksheet = writer.sheets["overview"]
                worksheet.autofit()
                worksheet.freeze_panes(1, 0)
            except Exception as e:
                logger.error(f"creating overview failed: {e}")

            for key, value in diff_dict.items():
                logger.debug(f"processing {key}")
                sheet_name = shorten_sheet_name(key)
                try:
                    value.to_excel(writer, sheet_name=sheet_name)
                    worksheet = writer.sheets[sheet_name]
                    worksheet.autofit()
                    worksheet.freeze_panes(1, 1)
                except Exception as e:
                    print(f"Error writing sheet {sheet_name}: {e}")
        logger.success("creating change excel file finished")
