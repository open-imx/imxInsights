# from lxml import etree as ET
from shapely import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry


def reverse_line(shapely_polyline: LineString) -> LineString:
    """
    Reverses the order of coordinates in a Shapely LineString object.

    Args:
        shapely_polyline (LineString): The LineString object to reverse.

    Returns:
        (LineString): A new LineString object with the coordinates in reverse order.

    """
    return LineString(list(shapely_polyline.coords)[::-1])


def compute_geometry_movement(
    geom1: Point
    | LineString
    | Polygon
    | MultiPoint
    | MultiLineString
    | MultiPolygon
    | GeometryCollection,
    geom2: Point
    | LineString
    | Polygon
    | MultiPoint
    | MultiLineString
    | MultiPolygon
    | GeometryCollection,
) -> BaseGeometry:
    """
    Compute a Shapely geometry representing the movement or difference between two geometries.

    :param geom1: The first geometry (Shapely object).
    :param geom2: The second geometry (Shapely object).
    :return: A Shapely geometry indicating the movement.
    """
    if geom1.geom_type != geom2.geom_type:
        raise ValueError(
            f"Cannot compare different geometry types: {geom1.geom_type} vs {geom2.geom_type}"
        )

    if geom1.is_empty or geom2.is_empty:
        return GeometryCollection()

    if geom1.geom_type == "Point":
        return LineString([geom1.coords[0], geom2.coords[0]])

    elif geom1.geom_type in {"LineString", "Polygon"}:
        return geom1.symmetric_difference(geom2)

    elif geom1.geom_type.startswith("Multi"):
        if hasattr(geom1, "geoms") and hasattr(geom2, "geoms"):
            parts1 = list(geom1.geoms)
            parts2 = list(geom2.geoms)

            movements = [
                compute_geometry_movement(p1, p2) for p1, p2 in zip(parts1, parts2)
            ]
            return GeometryCollection(movements)

    raise ValueError(
        f"Geometry type {geom1.geom_type} not supported for movement calculation."
    )
