import pyproj
from shapely import Geometry
from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)


class ShapelyTransform:
    """A utility class to transform between RD and WGS84 coordinate systems."""

    rd = pyproj.CRS("EPSG:28992")
    wgs = pyproj.CRS("EPSG:4326")
    _transformer_to_wgs = pyproj.Transformer.from_crs(rd, wgs, always_xy=True)
    _transformer_to_rd = pyproj.Transformer.from_crs(wgs, rd, always_xy=True)

    @classmethod
    def rd_to_wgs(
        cls,
        geometry: Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection,
    ) -> (
        Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection
    ):
        """
        Convert a Shapely geometry from RD (EPSG:28992) to WGS84 (EPSG:4326).

        Args:
            geometry: A Shapely geometry in RD coordinates.

        Returns:
            A Shapely geometry in WGS84 coordinates.
        """
        return cls._transform(geometry, cls._transformer_to_wgs)

    @classmethod
    def wgs_to_rd(
        cls,
        geometry: Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection,
    ) -> (
        Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection
    ):
        """
        Convert a Shapely geometry from WGS84 (EPSG:4326) to RD (EPSG:28992).

        Args:
            geometry: A Shapely geometry in WGS84 coordinates.

        Returns:
            A Shapely geometry in RD coordinates.
        """
        return cls._transform(geometry, cls._transformer_to_rd)

    @classmethod
    def _transform(
        cls,
        geometry: Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection
        | Geometry,
        transformer: pyproj.Transformer,
    ) -> (
        Point
        | LineString
        | Polygon
        | MultiLineString
        | MultiPoint
        | MultiPolygon
        | GeometryCollection
    ):
        if isinstance(geometry, Point):
            return cls._transform_point(geometry, transformer)

        elif isinstance(geometry, LineString):
            return cls._transform_linestring(geometry, transformer)

        elif isinstance(geometry, Polygon):
            return cls._transform_polygon(geometry, transformer)

        elif isinstance(geometry, MultiLineString):
            return cls._transform_multilinestring(geometry, transformer)

        elif isinstance(geometry, MultiPoint):
            return cls._transform_multipoint(geometry, transformer)

        elif isinstance(geometry, MultiPolygon):
            return cls._transform_multipolygon(geometry, transformer)

        elif isinstance(geometry, GeometryCollection):
            return cls._transform_geometrycollection(geometry, transformer)

        else:
            raise TypeError(f"Unsupported geometry type: {type(geometry).__name__}")  # NOQA TRY003

    @classmethod
    def _transform_coords(cls, coords, transformer):
        transformed_coords = []
        for coord in coords:
            if len(coord) == 2:
                x, y = coord
                transformed_coord = transformer.transform(x, y) + (0,)
            elif len(coord) == 3:
                x, y, z = coord
                transformed_coord = transformer.transform(x, y) + (z,)
            else:
                raise ValueError(  # NOQA TRY003
                    "Coordinate must have either 2 (x, y) or 3 (x, y, z) elements"
                )
            transformed_coords.append(transformed_coord)
        return transformed_coords

    @classmethod
    def _transform_point(cls, point: Point, transformer: pyproj.Transformer) -> Point:
        if point.has_z:
            x, y, z = point.x, point.y, point.z
            x, y = transformer.transform(x, y)
            return Point(x, y, z)
        else:
            x, y = transformer.transform(point.x, point.y)
            return Point(x, y)

    @classmethod
    def _transform_linestring(
        cls, linestring: LineString, transformer: pyproj.Transformer
    ) -> LineString:
        if linestring.has_z:
            return LineString(cls._transform_coords(linestring.coords, transformer))
        else:
            return LineString(
                [transformer.transform(x, y) for x, y in linestring.coords]
            )

    @classmethod
    def _transform_polygon(
        cls, polygon: Polygon, transformer: pyproj.Transformer
    ) -> Polygon:
        external_coords = cls._transform_coords(polygon.exterior.coords, transformer)

        holes = []
        for interior in iter(polygon.interiors):
            interior_coords = cls._transform_coords(interior.coords, transformer)
            holes.append(interior_coords)

        return Polygon(shell=external_coords, holes=holes)

    @classmethod
    def _transform_multilinestring(
        cls, multilinestring: MultiLineString, transformer: pyproj.Transformer
    ) -> MultiLineString:
        return MultiLineString(
            [
                cls._transform_linestring(linestring, transformer)
                for linestring in multilinestring.geoms
            ]
        )

    @classmethod
    def _transform_multipoint(
        cls, multipoint: MultiPoint, transformer: pyproj.Transformer
    ) -> MultiPoint:
        return MultiPoint(
            [cls._transform_point(point, transformer) for point in multipoint.geoms]
        )

    @classmethod
    def _transform_multipolygon(
        cls, multipolygon: MultiPolygon, transformer: pyproj.Transformer
    ) -> MultiPolygon:
        return MultiPolygon(
            [
                cls._transform_polygon(polygon, transformer)
                for polygon in multipolygon.geoms
            ]
        )

    @classmethod
    def _transform_geometrycollection(
        cls, geometrycollection: GeometryCollection, transformer: pyproj.Transformer
    ) -> GeometryCollection:
        return GeometryCollection(
            [
                cls._transform(geometry, transformer)
                for geometry in geometrycollection.geoms
            ]
        )
