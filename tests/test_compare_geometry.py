import pytest
from shapely.geometry import (
    Point, LineString, Polygon, MultiPoint, MultiPolygon, MultiLineString, GeometryCollection
)
from imxInsights.compare.geometryChange import GeometryChange, GeometryChangeStatus


def test_both_none():
    change = GeometryChange(t1=None, t2=None)
    assert change.status == GeometryChangeStatus.UNDEFINED


def test_t1_none():
    t2 = Point(1, 1)
    change = GeometryChange(t1=None, t2=t2)
    assert change.status == GeometryChangeStatus.ADDED


def test_t2_none():
    t1 = Point(1, 1)
    change = GeometryChange(t1=t1, t2=None)
    assert change.status == GeometryChangeStatus.REMOVED


def test_point_unchanged():
    t1 = Point(1, 1)
    t2 = Point(1, 1)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.UNCHANGED


def test_point_z_added():
    t1 = Point(1, 1)
    t2 = Point(1, 1, 1)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_ADDED


def test_point_z_removed():
    t1 = Point(1, 1, 1)
    t2 = Point(1, 1)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_REMOVED


def test_point_z_changed():
    t1 = Point(1, 1, 1)
    t2 = Point(1, 1, 2)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_CHANGED


def test_linestring_unchanged():
    coords = [(0, 0), (1, 1)]
    t1 = LineString(coords)
    t2 = LineString(coords)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.UNCHANGED


def test_linestring_changed():
    coords_t1 = [(0, 0), (1, 1)]
    coords_t2 = [(0, 0), (2, 2)]
    t1 = LineString(coords_t1)
    t2 = LineString(coords_t2)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.CHANGED


def test_linestring_z_added():
    coords_t1 = [(0, 0), (1, 1)]
    coords_t2 = [(0, 0, 1), (1, 1, 1)]
    t1 = LineString(coords_t1)
    t2 = LineString(coords_t2)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_ADDED


def test_polygon_unchanged():
    coords = [(0, 0), (1, 1), (1, 0)]
    t1 = Polygon(coords)
    t2 = Polygon(coords)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.UNCHANGED


def test_polygon_z_added():
    coords_t1 = [(0, 0), (1, 1), (1, 0)]
    coords_t2 = [(0, 0, 1), (1, 1, 1), (1, 0, 1)]
    t1 = Polygon(coords_t1)
    t2 = Polygon(coords_t2)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_ADDED


def test_multipoint_z_removed():
    t1 = MultiPoint([Point(0, 0, 1), Point(1, 1, 1)])
    t2 = MultiPoint([Point(0, 0), Point(1, 1)])
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.Z_REMOVED


# def test_geometrycollection_z_changed():
#     geometries_t1 = [
#         Point(0, 0, 4),
#         LineString([(0, 0, 2), (1, 1, 2)]),
#         Polygon([(0, 0, 5), (1, 1, 4), (1, 0, 5)])
#     ]
#     geometries_t2 = [
#         Point(0, 0, 1),
#         LineString([(0, 0, 3), (1, 1, 2)]),
#         Polygon([(0, 0, 1), (1, 1, 1), (1, 0, 1)])
#     ]
#     t1 = GeometryCollection(geometries_t1)
#     t2 = GeometryCollection(geometries_t2)
#     change = GeometryChange(t1=t1, t2=t2)
#     assert change.status == GeometryChangeStatus.Z_CHANGED


def test_geometrycollection_changed():
    geometries_t1 = [
        Point(0, 0),
        LineString([(0, 0), (1, 1)])
    ]
    geometries_t2 = [
        Point(1, 1),  # Change geometry
        LineString([(0, 0), (2, 2)])  # General change
    ]
    t1 = GeometryCollection(geometries_t1)
    t2 = GeometryCollection(geometries_t2)
    change = GeometryChange(t1=t1, t2=t2)
    assert change.status == GeometryChangeStatus.CHANGED



import pytest
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, GeometryCollection

from imxInsights.utils.shapely.shapley_helpers import compute_geometry_movement

# TODO: move to shaply diff test

def test_point_movement():
    point1 = Point(0, 0)
    point2 = Point(1, 1)
    movement = compute_geometry_movement(point1, point2)

    assert movement.geom_type == "LineString"
    assert list(movement.coords) == [(0, 0), (1, 1)]


def test_linestring_movement():
    line1 = LineString([(0, 0), (1, 0)])
    line2 = LineString([(0, 0), (0, 1)])
    movement = compute_geometry_movement(line1, line2)

    assert movement.geom_type == "MultiLineString" or movement.geom_type == "GeometryCollection"
    assert movement.is_valid


def test_polygon_movement():
    polygon1 = Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)])
    polygon2 = Polygon([(0.5, 0.5), (1.5, 0.5), (1.5, 1.5), (0.5, 1.5), (0.5, 0.5)])
    movement = compute_geometry_movement(polygon1, polygon2)

    assert movement.geom_type in {"Polygon", "MultiPolygon"}
    assert movement.is_valid


def test_multipoint_movement():
    multipoint1 = MultiPoint([(0, 0), (1, 1)])
    multipoint2 = MultiPoint([(1, 1), (2, 2)])
    movement = compute_geometry_movement(multipoint1, multipoint2)

    assert movement.geom_type == "GeometryCollection"
    assert all(geom.geom_type == "LineString" for geom in movement.geoms)


def test_invalid_geometry_types():
    point = Point(0, 0)
    line = LineString([(0, 0), (1, 0)])

    with pytest.raises(ValueError, match="Cannot compare different geometry types"):
        compute_geometry_movement(point, line)


def test_empty_geometries():
    empty_point = Point()
    non_empty_point = Point(1, 1)

    movement = compute_geometry_movement(empty_point, non_empty_point)
    assert movement.is_empty

    movement = compute_geometry_movement(non_empty_point, empty_point)
    assert movement.is_empty


def test_multilinestring_movement():
    multiline1 = MultiLineString([[(0, 0), (1, 0)], [(1, 1), (2, 2)]])
    multiline2 = MultiLineString([[(0, 0), (0, 1)], [(2, 2), (3, 3)]])
    movement = compute_geometry_movement(multiline1, multiline2)

    assert movement.geom_type == "GeometryCollection"
    assert all(geom.is_valid for geom in movement.geoms)


def test_no_movement():
    point = Point(1, 1)
    movement = compute_geometry_movement(point, point)
    assert movement.geom_type == "LineString"
    assert movement.length == 0
