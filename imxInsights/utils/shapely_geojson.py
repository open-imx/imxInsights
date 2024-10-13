from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import IO, cast

import orjson
from shapely import (  # MultiLineString,; MultiPoint,; MultiPolygon,
    LineString,
    Point,
    Polygon,
)
from shapely.geometry import mapping


class GeoJsonFeature:
    """
    A geojson feature build from one or more shapely geometries and a set of properties as a dictionary.

    !!! danger "Warning!"

        It's possible to use multi geometry types, but most applications wont support geojson multigeometry types, same as nested property dictionaries.

    Args:
        geometry_list: List of Shapley Geometries.
        properties: Optional dictionary of properties

    """

    def __init__(
        self,
        geometry_list: list[Point | LineString | Polygon],
        properties: dict | None = None,
    ) -> None:
        self.geometry_list = geometry_list
        self.properties = properties or {}

    @property
    def geometry_list(self) -> list[Point | LineString | Polygon]:
        """List of Shapely geometries that make up the feature."""
        return self._geometry_list

    @geometry_list.setter
    def geometry_list(self, geometries: list[Point | LineString | Polygon]) -> None:
        if not all(
            isinstance(geom, Point | LineString | Polygon) for geom in geometries
        ):
            raise ValueError("All geometries must be instances of Shapely geometries.")  # NOQA TRY003
        self._geometry_list = geometries

    @property
    def properties(self) -> dict:
        """Dictionary of properties associated with the feature."""
        return self._properties

    @properties.setter
    def properties(self, props: dict | None) -> None:
        if props is None:
            self._properties = {}
        elif not isinstance(props, dict):
            raise ValueError("Properties must be a dictionary.")  # NOQA TRY003
        else:
            self._properties = props

    @property
    def __geo_interface__(self) -> dict:
        geometries = self._get_geo_interface()
        if len(self.geometry_list) > 1:
            geometry = {"type": "GeometryCollection", "geometries": geometries}
        else:
            geometry = {"geometry": geometries}

        return {
            "type": "Feature",
            "properties": self.properties,
        } | geometry

    def _get_geo_interface(
        self,
    ) -> None | list[dict]:
        geometries: list[dict] = []

        if len(self.geometry_list) == 0:
            return None

        elif len(self.geometry_list) > 1:
            for item in self.geometry_list:
                geometries.append(item.__geo_interface__)

        else:
            if self.geometry_list[0].is_empty:
                return None
            else:
                geometries.append(
                    self.geometry_list[0].__geo_interface__
                )  # Append to the list.

        return geometries if geometries else None  # Return None if the list is empty.

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoJsonFeature):
            return NotImplemented
        return self.__geo_interface__ == other.__geo_interface__

    def __repr__(self) -> str:
        return f"<GeoJsonFeature {self.__geo_interface__}>"

    def as_dict(self) -> dict:
        """Return the GeoJSON representation as a dictionary.

        Returns:
            dict: The GeoJSON dictionary representation of the feature.
        """
        return self.__geo_interface__


class GeoJsonFeatureCollection:
    """
    GeoJson FeatureCollection stores geojson Features.

    Args:
        geojson_features: List of GeoJsonFeatures or BaseGeometry objects.
        crs: Optional CRS that will be included in the geojson.
    """

    def __init__(
        self,
        geojson_features: list[GeoJsonFeature | Point | LineString | Polygon],
        crs: CrsEnum | None = None,
    ) -> None:
        self.features: list[GeoJsonFeature] = []
        self.features = [self._to_geojson_feature(item) for item in geojson_features]
        self.crs = crs

    @property
    def features(self) -> list[GeoJsonFeature]:
        """List of GeoJsonFeatures in the collection."""
        return self._features

    @features.setter
    def features(
        self, items: list[GeoJsonFeature | Point | LineString | Polygon]
    ) -> None:
        """
        Set the features in the collection.

        Args:
            items (list[GeoJsonFeature | BaseGeometry]): List of GeoJsonFeatures or geometries.
        """
        self._features = [
            item
            if isinstance(item, GeoJsonFeature)
            else GeoJsonFeature([cast(Point | LineString | Polygon, item)])
            for item in items
        ]

    @staticmethod
    def _to_geojson_feature(
        item: GeoJsonFeature | Point | LineString | Polygon,
    ) -> GeoJsonFeature:
        if isinstance(item, GeoJsonFeature):
            return item
        return GeoJsonFeature([cast(Point | LineString | Polygon, item)])

    def _get_crs_dict(self) -> dict:
        return {
            "crs": {
                "type": "name",
                "properties": {"name": f"urn:ogc:def:crs:EPSG::{self.crs}"},
            }
        }

    @property
    def __geo_interface__(self) -> dict:
        crs_dict = self._get_crs_dict() if self.crs is not None else {}
        return crs_dict | {
            "type": "FeatureCollection",
            "features": [feature.__geo_interface__ for feature in self.features],
        }

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, GeoJsonFeatureCollection):
            return NotImplemented
        return self.__geo_interface__ == other.__geo_interface__

    def __len__(self) -> int:
        return len(self.features)

    def __repr__(self) -> str:
        return f"<GeoJsonFeatureCollection {self.features}>"

    def as_dict(self) -> dict:
        """Return the FeatureCollection as a dictionary.

        Returns:
            The GeoJSON FeatureCollection representation.
        """
        return self.__geo_interface__

    @staticmethod
    def _dump(
        feature_collection: GeoJsonFeatureCollection,
        file_path: IO[str],
        *args,
        **kwargs,
    ) -> None:
        """
        Dump a FeatureCollection to a file as GeoJSON.

        Args:
            feature_collection: The feature collection to dump.
            file_path: The output file path.

        """

    def as_string(self) -> str:
        """Convert the instance to a GeoJSON string representation.

        Returns:
            A GeoJSON-formatted string representing the instance.
        """
        return orjson.dumps(
            mapping(self), default=default, option=orjson.OPT_INDENT_2
        ).decode("utf-8")

    def to_file(self, file_path: str | Path) -> None:
        """Writes the collection to a GeoJSON file."""
        with open(file_path, mode="w") as file:
            file.write(self.as_string())


class CrsEnum(Enum):
    """Enumeration of Coordinate Reference Systems (CRS) with their corresponding EPSG codes."""

    WGS84 = "4326"
    """World Geodetic System 1984 (WGS 84) - EPSG:4326."""

    RD_NEW = "28992"
    """Amersfoort / RD New (Rijksdriehoeksstelsel) - EPSG:28992."""

    RD_NEW_NAP = "7415"
    """Amersfoort / RD New (Rijksdriehoeksstelsel) + NAP (Normaal Amsterdams Peil) - EPSG:7415."""


def default(obj):
    """Return the WKT representation of Shapely geometries or call the superclass method.

    Args:
        obj: The object to encode.

    Returns:
        WKT representation of the geometry if it's a Shapely object, otherwise invokes the default encoder.
    """
    if isinstance(obj, Point | LineString | Polygon):
        if hasattr(obj, "wkt"):
            return obj.wkt


feature_point = GeoJsonFeature([Point(1, 1)], {"name": "Point Feature"})
feature_line = GeoJsonFeature(
    [LineString([(0, 0), (1, 1), (2, 2)])], {"name": "LineString Feature"}
)
collection = GeoJsonFeatureCollection(
    [feature_point, feature_line], crs=CrsEnum.RD_NEW_NAP
)
geojson_str = collection.as_string()

print()
