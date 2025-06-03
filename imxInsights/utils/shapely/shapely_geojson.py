from enum import Enum
from pathlib import Path

import geojson as geojson_dependency
from geojson import Feature as GeoJsonFeature
from geojson import FeatureCollection as GeoJsonFeatureCollection
from geojson import GeometryCollection as GeoJsonGeometryCollection
from geojson import LineString as GeoJsonLineString
from geojson import MultiLineString as GeoJsonMultiLineString
from geojson import MultiPoint as GeoJsonMultiPoint
from geojson import MultiPolygon as GeoJsonMultiPolygon
from geojson import Point as GeoJsonPoint
from geojson import Polygon as GeoJsonPolygon
from geojson import dump as geojson_dump
from geojson import dumps as geojson_dumps
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

geojson_dependency.geometry.DEFAULT_PRECISION = 16


class ShapelyGeoJsonFeature:
    """
    A class to represent a GeoJSON feature with Shapely geometries.

    Args:
        geometry_list (list[Point | LineString | Polygon]):
            A list of Shapely geometry objects (Point, LineString, or Polygon).
        properties (dict | None, optional):
            A dictionary of properties associated with the feature. Default is None.
    """

    def __init__(
        self,
        geometry_list: list[
            Point
            | LineString
            | Polygon
            | MultiLineString
            | MultiPoint
            | MultiPolygon
            | GeometryCollection
        ],
        properties: dict | None = None,
    ) -> None:
        self._geometry_list = []
        if geometry_list:
            for geom in geometry_list:
                if isinstance(geom, Point | LineString | Polygon):
                    self._geometry_list.append(geom)
                else:
                    raise ValueError("geometry is not a shapley geometry")  # NOQA TRY004 TRY003

        self.properties = properties or {}

    @property
    def geometry_list(self) -> list[Point | LineString | Polygon]:
        """
        Get the list of geometries.

        Returns:
            list[Point | LineString | Polygon]:
                The list of Shapely geometries.
        """
        return self._geometry_list

    @property
    def properties(self) -> dict:
        """
        Get the properties of the feature.

        Returns:
            dict:
                The properties associated with the feature.
        """
        return self._properties

    @properties.setter
    def properties(self, props: dict | None) -> None:
        """
        Set the properties of the feature.

        Args:
            props (dict | None):
                A dictionary of properties to set. If None, the properties will be cleared.

        Raises:
            ValueError:
                If props is not a dictionary.
        """
        if props is None:
            self._properties = {}
        elif not isinstance(props, dict):
            raise ValueError("Properties must be a dictionary.")  # NOQA TRY003
        else:
            self._properties = props

    @staticmethod
    def _get_point_coordinates(point_item: Point):
        return list(point_item.coords)

    @staticmethod
    def _get_line_coordinates(line_item: LineString):
        return list(line_item.coords)

    @staticmethod
    def _get_polygon_coordinates(polygon_item: Polygon):
        polygon_entries = [tuple(polygon_item.exterior.coords)]
        for i, hole in enumerate(polygon_item.interiors):
            polygon_entries.append(tuple(hole.coords))
        return polygon_entries

    def as_feature(self) -> GeoJsonFeature:
        """
        Convert the ShapelyGeoJsonFeature to a GeoJSON feature.

        Returns:
            The corresponding GeoJSON feature representation.

        """
        if not self.geometry_list:
            return GeoJsonFeature(geometry=None, properties=self.properties)

        # point feature
        elif len(self.geometry_list) == 1 and isinstance(self.geometry_list[0], Point):
            return GeoJsonFeature(
                geometry=GeoJsonPoint(
                    *self._get_point_coordinates(self.geometry_list[0])
                ),
                properties=self.properties,
            )
        elif all(isinstance(geom, Point) for geom in self.geometry_list):
            return GeoJsonFeature(
                geometry=GeoJsonMultiPoint(
                    *[self._get_point_coordinates(_) for _ in self.geometry_list]  # type: ignore[arg-type]
                ),
                properties=self.properties,
            )

        # line feature
        elif len(self.geometry_list) == 1 and isinstance(
            self.geometry_list[0], LineString
        ):
            return GeoJsonFeature(
                geometry=GeoJsonLineString(
                    *[
                        self._get_line_coordinates(geom)
                        for geom in self.geometry_list
                        if isinstance(geom, LineString)
                    ]
                ),
                properties=self.properties,
            )
        elif all(isinstance(geom, LineString) for geom in self.geometry_list):
            return GeoJsonFeature(
                geometry=GeoJsonMultiLineString(
                    [tuple(geom.coords) for geom in self.geometry_list]
                ),
                properties=self.properties,
            )

        # polygon feature
        elif len(self.geometry_list) == 1 and isinstance(
            self.geometry_list[0], Polygon
        ):
            return GeoJsonFeature(
                geometry=GeoJsonPolygon(
                    *[
                        self._get_polygon_coordinates(geom)
                        for geom in self.geometry_list
                        if isinstance(geom, Polygon)
                    ]
                ),
                properties=self.properties,
            )
        elif all(isinstance(geom, Polygon) for geom in self.geometry_list):
            return GeoJsonFeature(
                geometry=GeoJsonMultiPolygon(
                    [*[self._get_polygon_coordinates(_) for _ in self.geometry_list]]  # type: ignore[arg-type]
                ),
                properties=self.properties,
            )

        # geometry collection feature
        else:
            geometries = []
            for item in self.geometry_list:
                if isinstance(item, Point):
                    geometries.append(GeoJsonPoint(*self._get_point_coordinates(item)))
                elif isinstance(item, LineString):
                    geometries.append(
                        GeoJsonLineString(self._get_line_coordinates(item))
                    )
                elif isinstance(item, Polygon):
                    geometries.append(
                        GeoJsonPolygon(self._get_polygon_coordinates(item))
                    )

            return GeoJsonFeature(
                geometry=GeoJsonGeometryCollection(geometries),
                properties=self.properties,
            )


class CrsEnum(Enum):
    """Enumeration of Coordinate Reference Systems (CRS) with their corresponding EPSG codes."""

    WGS84 = "4326"
    """World Geodetic System 1984 (WGS 84) - EPSG:4326."""

    RD_NEW = "28992"
    """Amersfoort / RD New (Rijksdriehoeksstelsel) - EPSG:28992."""

    RD_NEW_NAP = "7415"
    """Amersfoort / RD New (Rijksdriehoeksstelsel) + NAP (Normaal Amsterdams Peil) - EPSG:7415."""


class ShapelyGeoJsonFeatureCollection:
    """
    Shapley GeoJson FeatureCollection stores geojson Features.

    Args:
        features: List of GeoJsonFeatures or BaseGeometry objects.
        crs: Optional CRS that will be included in the geojson.
    """

    def __init__(
        self,
        features: list[ShapelyGeoJsonFeature],
        crs: CrsEnum | None = None,
    ) -> None:
        self.features: list[ShapelyGeoJsonFeature] = features
        self.crs = crs

    def _as_feature_collection(self):
        if self.crs:
            return FeatureCollection(
                [_.as_feature() for _ in self.features], crs=self.crs
            )
        return FeatureCollection([_.as_feature() for _ in self.features])

    def geojson_str(self) -> str:
        """Generate a GeoJSON string representation of the FeatureCollection.

        Returns:
            A string containing the GeoJSON representation of the FeatureCollection.

        """
        return geojson_dumps(self._as_feature_collection(), sort_keys=True)

    def to_geojson_file(self, file_path: str | Path) -> None:
        """Write the FeatureCollection to a GeoJSON file.

        Args:
            file_path: The path where the GeoJSON file will be saved.

        """
        with open(file_path, mode="w") as file:
            geojson_dump(self._as_feature_collection(), file, indent=4)


class FeatureCollection(GeoJsonFeatureCollection):
    """Custom FeatureCollection that adds a crs string (old geojson spec)."""

    def __init__(self, features, **extra):
        super().__init__(features, **extra)
        if "crs" in extra:
            self["crs"] = {
                "type": "name",
                "properties": {"name": f"urn:ogc:def:crs:EPSG::{extra['crs'].value}"},
            }
