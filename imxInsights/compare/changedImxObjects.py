from pathlib import Path

import pandas as pd

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.utils.excel_helpers import clean_diff_df
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    styler_highlight_changes,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)


class ChangedImxObjects:
    def __init__(self, compared_objects: list[ChangedImxObject]):
        self.compared_objects: list[ChangedImxObject] = compared_objects

    def get_geojson(
        self,
        object_path: list[str] | None = None,
        as_wgs: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        if object_path:
            features = self._get_features_by_path(object_path, as_wgs=as_wgs)
        else:
            # todo: rename to_wgs
            features = [
                item.as_geojson_feature(as_wgs=as_wgs) for item in self.compared_objects
            ]

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if as_wgs else CrsEnum.RD_NEW_NAP
        )

    def _get_features_by_path(
        self,
        object_path: list[str],
        as_wgs: bool = True,
    ) -> list[ShapelyGeoJsonFeature]:
        features = []
        for item in self.compared_objects:
            if item.t1 and item.t1.path in object_path:
                features.append(item.as_geojson_feature(as_wgs=as_wgs))
            if item.t2 and item.t2.path in object_path:
                features.append(item.as_geojson_feature(as_wgs=as_wgs))
        return features

    def create_geojson_files(
        self,
        directory_path: str | Path,
        as_wgs: bool = True,
    ) -> None:
        paths = []
        for obj in self.compared_objects:
            if obj.t1:
                paths.append(obj.t1.path)
            if obj.t2:
                paths.append(obj.t2.path)
        paths = list(set(paths))

        dir_path = Path(directory_path)
        dir_path.mkdir(parents=True, exist_ok=True)

        for path in paths:
            geojson_collection = self.get_geojson([path], as_wgs)
            geojson_collection.to_geojson_file(dir_path / f"{path}.geojson")

    def get_overview_df(self) -> pd.DataFrame:
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
        valid_columns = [col for col in columns_to_keep if col in df.columns]
        df = df[valid_columns]
        df = df.fillna("")
        df = df.style.map(styler_highlight_changes)  # type: ignore[attr-defined]
        return df

    def get_all_object_paths(self) -> list[str]:
        return sorted(
            [
                obj.path
                for item in self.compared_objects
                for obj in (item.t1, item.t2)
                if obj
            ]
        )

    def get_change_df(self, object_path: list[str]) -> pd.DataFrame:
        items = [
            item
            for item in self.compared_objects
            if (item.t1 and item.t1.path in object_path)
            or (item.t2 and item.t2.path in object_path)
        ]

        out = [item.get_change_dict() for item in items]
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

            df = df.style.map(styler_highlight_changes)  # type: ignore[attr-defined]

        return df
