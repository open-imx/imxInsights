import pytest
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon, GeometryCollection
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform  # Adjust the import to the actual module name
from imxInsights.utils.shapely.shapely_gml import GmlShapelyFactory


def test_rs_wgs_point_no_z():
    rd_point = Point(GmlShapelyFactory.gml_point_to_shapely("209021.633,461739.949"))
    wgs_point = ShapelyTransform.rd_to_wgs(rd_point)
    rd_point_back = ShapelyTransform.wgs_to_rd(wgs_point)
    assert rd_point_back.equals_exact(rd_point, 3), "Round trip should result the same"

def test_rs_wgs_point():
    rd_point = Point(GmlShapelyFactory.gml_point_to_shapely("209021.633,461739.949,15.015"))
    wgs_point = ShapelyTransform.rd_to_wgs(rd_point)
    rd_point_back = ShapelyTransform.wgs_to_rd(wgs_point)
    assert rd_point_back.equals_exact(rd_point, 3), "Round trip should result the same"

def test_rs_wgs_linestring_no_z():
    rd_linestring = LineString(GmlShapelyFactory.gml_linestring_to_shapely("210427.279,462296.441 210422.279,462291.441 210414.566,462281.001"))
    wgs_linestring = ShapelyTransform.rd_to_wgs(rd_linestring)
    rd_linestring_back = ShapelyTransform.wgs_to_rd(wgs_linestring)
    assert rd_linestring.equals_exact(rd_linestring_back, 3), "Round trip should result the same"

def test_rs_wgs_linestring():
    rd_linestring = LineString(GmlShapelyFactory.gml_linestring_to_shapely("210427.279,462296.441,10.977 210414.566,462281.001,11.058"))
    wgs_linestring = ShapelyTransform.rd_to_wgs(rd_linestring)
    rd_linestring_back = ShapelyTransform.wgs_to_rd(wgs_linestring)
    assert rd_linestring.equals_exact(rd_linestring_back, 3), "Round trip should result the same"

def test_rs_wgs_polygon():
    # polygon donut
    exterior_coords = [(0, 0, 1), (0, 10, 1), (10, 10, 1), (10, 0, 1)]
    holes = [
        [(2, 2, 1), (2, 4, 1), (4, 4, 1), (4, 2, 1)],  # First hole
        [(6, 6), (6, 8), (8, 8), (8, 6)],  # Second hole
        [(3, 7), (3, 9), (5, 9), (5, 7)]  # Third hole
    ]
    rd_polygon = Polygon(shell=exterior_coords, holes=holes)
    wgs_polygon = ShapelyTransform.rd_to_wgs(rd_polygon)
    rd_polygon_back = ShapelyTransform.wgs_to_rd(wgs_polygon)
    assert rd_polygon.equals_exact(rd_polygon_back, 3), "Round trip should result the same"


def test_rd_wgs_multilinestring():
    rd_multilinestring = MultiLineString(
        [
            LineString(GmlShapelyFactory.gml_linestring_to_shapely("210427.279,462296.441 210414.566,462281.001")),
            LineString(GmlShapelyFactory.gml_linestring_to_shapely("210400.000,462300.000 210380.000,462280.000"))
        ]
    )
    wgs_multilinestring = ShapelyTransform.rd_to_wgs(rd_multilinestring)
    rd_multilinestring_back = ShapelyTransform.wgs_to_rd(wgs_multilinestring)
    for rd_back, rd_original in zip(rd_multilinestring_back.geoms, rd_multilinestring.geoms):
        assert rd_back.equals_exact(rd_original, 3), "Round trip should result the same"


def test_rd_wgs_multipoint():
    rd_multipoint = MultiPoint(
        [
            Point(GmlShapelyFactory.gml_point_to_shapely("209021.633,461739.949")),
            Point(GmlShapelyFactory.gml_point_to_shapely("210021.633,462739.949"))
        ]
    )
    wgs_multipoint = ShapelyTransform.rd_to_wgs(rd_multipoint)
    rd_multipoint_back = ShapelyTransform.wgs_to_rd(wgs_multipoint)
    for rd_back, rd_original in zip(rd_multipoint_back.geoms, rd_multipoint.geoms):
        assert rd_back.equals_exact(rd_original, 3), "Round trip should result the same"

def test_rd_wgs_multipolygon():
    rd_multipolygon = MultiPolygon(
        [
            Polygon(shell=[(0, 0), (0, 10), (10, 10), (10, 0)]),
            Polygon(shell=[(20, 20), (20, 30), (30, 30), (30, 20)])
        ]
    )
    wgs_multipolygon = ShapelyTransform.rd_to_wgs(rd_multipolygon)
    rd_multipolygon_back = ShapelyTransform.wgs_to_rd(wgs_multipolygon)
    # Iterate over individual Polygons for comparison
    for rd_back, rd_original in zip(rd_multipolygon_back.geoms, rd_multipolygon.geoms):
        assert rd_back.equals_exact(rd_original, 3), "Round trip should result the same"

def test_rd_wgs_geometrycollection():
    rd_geometrycollection = GeometryCollection(
        [
            Point(GmlShapelyFactory.gml_point_to_shapely("209021.633,461739.949")),
            LineString(GmlShapelyFactory.gml_linestring_to_shapely("210427.279,462296.441 210414.566,462281.001")),
            Polygon(shell=[(0, 0), (0, 10), (10, 10), (10, 0)])
        ]
    )
    wgs_geometrycollection = ShapelyTransform.rd_to_wgs(rd_geometrycollection)
    rd_geometrycollection_back = ShapelyTransform.wgs_to_rd(wgs_geometrycollection)
    # Iterate over individual geometries in the collection for comparison
    for rd_back, rd_original in zip(rd_geometrycollection_back.geoms, rd_geometrycollection.geoms):
        assert rd_back.equals_exact(rd_original, 3), "Round trip should result the same"