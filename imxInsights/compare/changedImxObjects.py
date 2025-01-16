from pathlib import Path
import pandas as pd


from imxInsights.compare.changedImxObject import ChangedImxObject
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
        to_wgs: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        if object_path:
            features = self._get_features_by_path(object_path)
        else:
            features = [item.as_geojson_feature() for item in self.compared_objects]

        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def _get_features_by_path(
        self, object_path: list[str]
    ) -> list[ShapelyGeoJsonFeature]:
        features = []
        for item in self.compared_objects:
            if item.t1 and item.t1.path in object_path:
                features.append(item.as_geojson_feature())
            if item.t2 and item.t2.path in object_path:
                features.append(item.as_geojson_feature())
        return features

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
    ):
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
            geojson_collection = self.get_geojson([path], to_wgs)
            geojson_collection.to_geojson_file(dir_path / f"{path}.geojson")

    def get_overview(self):
        out = []
        for item in self.compared_objects:
            path = ""
            if item.t1:
                path = item.t1.path
            if item.t2:
                if path != item.t2.path:
                    path = f"{path}/{item.t2.path}"

            out.append([item.puic, path, item.status.name])

        return pd.DataFrame(out, columns=["puic", "path", "change_status"])
