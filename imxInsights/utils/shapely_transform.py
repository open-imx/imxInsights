import pyproj
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
    ) -> Point | LineString | Polygon | MultiLineString | MultiPoint | MultiPolygon:
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
    ) -> Point | LineString | Polygon | MultiLineString | MultiPoint | MultiPolygon:
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
        | GeometryCollection,
        transformer: pyproj.Transformer,
    ) -> Point | LineString | Polygon | MultiLineString | MultiPoint | MultiPolygon:
        """
        Apply coordinate transformation to the given geometry using the provided transformer.

        Args:
            geometry: A Shapely geometry (Point, LineString, Polygon).
            transformer: A pyproj Transformer for coordinate transformation.

        Returns:
            A transformed Shapely geometry.
        """
        if isinstance(geometry, Point):
            if geometry.has_z:
                x, y, z = geometry.x, geometry.y, geometry.z
                x, y = transformer.transform(x, y)
                return Point(x, y, z)
            else:
                x, y = transformer.transform(geometry.x, geometry.y)
                return Point(x, y)

        elif isinstance(geometry, LineString):
            if geometry.has_z:
                transformed_coords: list[tuple[float, float, float]] = []

                for coord in geometry.coords:
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

                return LineString(transformed_coords)

            else:
                return LineString(
                    [transformer.transform(x, y) for x, y in geometry.coords]
                )

        elif isinstance(geometry, Polygon):
            raise NotImplementedError(f"{geometry} not implemented")

        else:
            raise TypeError(f"Unsupported geometry type: {type(geometry).__name__}")  # NOQA TRY003
