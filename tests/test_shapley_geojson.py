import pytest

from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeature, ShapelyGeoJsonFeatureCollection, CrsEnum
from shapely import Point, LineString, Polygon


def test_point_features():
    # test point features:
    point = ShapelyGeoJsonFeature([Point(0, 1, 2)])
    point_feature = point.as_feature()
    assert point_feature.is_valid

    multi_point = ShapelyGeoJsonFeature([Point(0, 1, 2), Point(2, 3, 0)])
    multi_point_feature = multi_point.as_feature()
    assert multi_point_feature.is_valid

def test_line_features():
    # test line features:
    line = ShapelyGeoJsonFeature([LineString([(0, 0, 0), (1, 1, 1)])])
    line_feature = line.as_feature()
    assert line_feature.is_valid

    multi_line = ShapelyGeoJsonFeature([LineString([(0, 0, 0), (1, 1, 1)]), LineString([(1, 2), (3, 4)])])
    multi_line_feature = multi_line.as_feature()
    assert multi_line_feature.is_valid

def test_polygon_features():
    # test polygon
    polygon_no_hole = ShapelyGeoJsonFeature([Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])])
    polygon_no_hole_feature = polygon_no_hole.as_feature()
    assert polygon_no_hole_feature.is_valid

    # polygon donut
    exterior_coords = [(0, 0, 1), (0, 10, 1), (10, 10, 1), (10, 0, 1)]
    holes = [
        [(2, 2, 1), (2, 4, 1), (4, 4, 1), (4, 2, 1)],  # First hole
        [(6, 6), (6, 8), (8, 8), (8, 6)],  # Second hole
        [(3, 7), (3, 9), (5, 9), (5, 7)]  # Third hole
    ]
    polygon_with_multiple_holes = ShapelyGeoJsonFeature([Polygon(shell=exterior_coords, holes=holes)])
    polygon_with_multiple_holes_feature = polygon_with_multiple_holes.as_feature()
    assert polygon_with_multiple_holes_feature.is_valid

    # multi polygon
    multi_polygon_no_hole = ShapelyGeoJsonFeature([
        Polygon([(0, 0), (0, 5), (5, 5), (5, 0)]),
        Polygon([(0, 0, 1), (0, 10, 1), (10, 10, 1), (10, 0, 1)])
    ])
    multi_polygon_no_hole_feature = multi_polygon_no_hole.as_feature()
    assert multi_polygon_no_hole_feature.is_valid

    # # multi polygon donut
    exterior_coords = [(0, 0, 1), (0, 10, 1), (10, 10, 1), (10, 0, 1)]
    holes = [
        [(2, 2, 1), (2, 4, 1), (4, 4, 1), (4, 2, 1)],  # First hole
        [(6, 6), (6, 8), (8, 8), (8, 6)],  # Second hole
        [(3, 7), (3, 9), (5, 9), (5, 7)]  # Third hole
    ]
    polygon_with_multiple_holes = Polygon(shell=exterior_coords, holes=holes)
    polygon_no_hole = Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])
    multi_polygon_hole = ShapelyGeoJsonFeature([polygon_with_multiple_holes, polygon_no_hole])
    multi_polygon_hole_feature = multi_polygon_hole.as_feature()
    assert multi_polygon_hole_feature.is_valid

def test_geometry_collection():
    point = Point(0, 1, 2)
    line = LineString([(0, 0, 0), (1, 1, 1)])
    polygon = Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])

    geometry_collection = ShapelyGeoJsonFeature([line, point, polygon])
    geometry_collection_feature = geometry_collection.as_feature()
    assert geometry_collection_feature.is_valid


def test_feature_collection():
    point = ShapelyGeoJsonFeature([Point(0, 1, 2)])
    line = ShapelyGeoJsonFeature([LineString([(0, 0, 0), (1, 1, 1)])])
    polygon = ShapelyGeoJsonFeature([Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])])
    multi_point = ShapelyGeoJsonFeature([Point(0, 1, 2), Point(2, 3, 0)])

    shapely_point = Point(0, 1, 2)
    shapely_line = LineString([(0, 0, 0), (1, 1, 1)])
    shapely_polygon = Polygon([(0, 0), (0, 5), (5, 5), (5, 0)])
    geometry_collection = ShapelyGeoJsonFeature([shapely_point, shapely_line, shapely_polygon])

    collection = ShapelyGeoJsonFeatureCollection([point, line, polygon, multi_point, geometry_collection])
    tester_1 = collection._as_feature_collection()
    assert len(tester_1['features']) == 5, "Should have x features"
    tester_2 = collection.geojson_str()
    assert '"type": "FeatureCollection"' in tester_2, "Should contain type: FeatureCollection"
    collection.crs = CrsEnum.WGS84
    tester_3 = collection.geojson_str()
    assert '"crs": {"properties":' in tester_3, "Should contain CRS"
    # collection.to_geojson_file("tester.geojson")
