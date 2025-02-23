from typing import cast

import numpy as np
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


def get_azimuth_from_points(point1: Point, point2: Point) -> float:
    """
    Calculates the azimuth angle between two points.

    Args:
        point1 (Point): The first Point object.
        point2 (Point): The second Point object.

    Returns:
        (float): The azimuth angle in degrees.

    """
    angle = np.arctan2(point2.x - point1.x, point2.y - point1.y)
    return float(np.degrees(angle)) if angle >= 0 else float(np.degrees(angle) + 360)


def cut(line: LineString, distance: float) -> list[LineString]:
    if distance == 0:
        return [line]

    if distance <= 0.0 or distance >= line.length:
        return [LineString(line)]

    coordinates = list(line.coords)
    has_z = (
        len(coordinates[0]) == 3
    )  # Check if the original coordinates have a Z dimension

    for i, p in enumerate(coordinates):
        pd = line.project(Point(p))
        if pd == distance:
            return [LineString(coordinates[: i + 1]), LineString(coordinates[i:])]
        if pd > distance:
            cp = line.interpolate(distance)
            if has_z:
                new_point_3d = (cp.x, cp.y, cp.z)
                # Cast coordinates to list of 3D tuples
                coords_3d = cast(list[tuple[float, float, float]], coordinates)
                return [
                    LineString(coords_3d[:i] + [new_point_3d]),
                    LineString([new_point_3d] + coords_3d[i:]),
                ]
            else:
                new_point_2d = (cp.x, cp.y)
                # Cast coordinates to list of 2D tuples
                coords_2d = cast(list[tuple[float, float]], coordinates)
                return [
                    LineString(coords_2d[:i] + [new_point_2d]),
                    LineString([new_point_2d] + coords_2d[i:]),
                ]

    return []


def cut_profile(line: LineString, measure_from: float, measure_to: float) -> LineString:
    if measure_from > measure_to:
        measure_from, measure_to = measure_to, measure_from
    if measure_from == 0:
        new_line = line
    else:
        new_line = cut(line, measure_from)[1]

    point = line.interpolate(measure_to)
    new_measure = new_line.project(point)
    result = cut(new_line, new_measure)[0]
    return result
