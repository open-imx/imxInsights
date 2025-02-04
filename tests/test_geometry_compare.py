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
