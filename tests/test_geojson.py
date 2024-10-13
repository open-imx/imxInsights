import pytest
from shapely.geometry import Point, LineString
from imxInsights.utils.shapely_transform import ShapelyTransform  # Adjust the import to the actual module name
from imxInsights.utils.shapely_gml import GmlShapleyFactory


def test_rs_wgs_point_no_z():
    rd_point = Point(GmlShapleyFactory.gml_point_to_shapely("209021.633,461739.949"))
    wgs_point = ShapelyTransform.rd_to_wgs(rd_point)
    rd_point_back = ShapelyTransform.wgs_to_rd(wgs_point)
    assert rd_point_back.equals_exact(rd_point, 3), "Round trip should result the same"

def test_rs_wgs_point():
    rd_point = Point(GmlShapleyFactory.gml_point_to_shapely("209021.633,461739.949,15.015"))
    wgs_point = ShapelyTransform.rd_to_wgs(rd_point)
    rd_point_back = ShapelyTransform.wgs_to_rd(wgs_point)
    assert rd_point_back.equals_exact(rd_point, 3), "Round trip should result the same"

def test_rs_wgs_linestring_no_z():
    rd_linestring = LineString(GmlShapleyFactory.gml_linestring_to_shapely("210427.279,462296.441 210422.279,462291.441 210414.566,462281.001"))
    wgs_linestring = ShapelyTransform.rd_to_wgs(rd_linestring)
    rd_linestring_back = ShapelyTransform.wgs_to_rd(wgs_linestring)
    assert rd_linestring.equals_exact(rd_linestring_back, 3), "Round trip should result the same"

def test_rs_wgs_linestring():
    rd_linestring = LineString(GmlShapleyFactory.gml_linestring_to_shapely("210427.279,462296.441,10.977 210414.566,462281.001,11.058"))
    wgs_linestring = ShapelyTransform.rd_to_wgs(rd_linestring)
    rd_linestring_back = ShapelyTransform.wgs_to_rd(wgs_linestring)
    assert rd_linestring.equals_exact(rd_linestring_back, 3), "Round trip should result the same"

