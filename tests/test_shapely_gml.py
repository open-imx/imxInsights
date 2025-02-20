import pytest
from lxml import etree
from shapely.geometry import Point, LineString, Polygon, MultiPoint, MultiLineString, MultiPolygon

from imxInsights.utils.shapely.shapely_gml import GmlShapelyFactory


@pytest.mark.parametrize(
    "coord_text, expected",
    [
        ("1,2", [(1.0, 2.0)]),
        ("1,2 3,4", [(1.0, 2.0), (3.0, 4.0)]),
        ("-1,-2 5,6", [(-1.0, -2.0), (5.0, 6.0)]),
    ],
)
def test_parse_coordinates(coord_text, expected):
    assert GmlShapelyFactory.parse_coordinates(coord_text) == expected

@pytest.mark.parametrize(
    "coord_text, expected",
    [
        ("1,2", Point(1.0, 2.0)),
        ("3.5,4.5", Point(3.5, 4.5)),
    ],
)
def test_gml_point_to_shapely(coord_text, expected):
    assert GmlShapelyFactory.gml_point_to_shapely(coord_text).equals(expected)

@pytest.mark.parametrize(
    "coord_text, expected",
    [
        ("1,2 3,4", LineString([(1.0, 2.0), (3.0, 4.0)])),
        ("0,0 1,1 2,2", LineString([(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)])),
    ],
)
def test_gml_linestring_to_shapely(coord_text, expected):
    assert GmlShapelyFactory.gml_linestring_to_shapely(coord_text).equals(expected)

def test_gml_polygon_to_shapely():
    gml_polygon = """
    <Polygon xmlns="http://www.opengis.net/gml">
        <outerBoundaryIs>
            <LinearRing>
                <coordinates>0,0 4,0 4,4 0,4 0,0</coordinates>
            </LinearRing>
        </outerBoundaryIs>
        <innerBoundaryIs>
            <LinearRing>
                <coordinates>1,1 3,1 3,3 1,3 1,1</coordinates>
            </LinearRing>
        </innerBoundaryIs>
    </Polygon>
    """
    root = etree.fromstring(gml_polygon)
    polygon = GmlShapelyFactory.gml_polygon_to_shapely(root)
    expected = Polygon([(0, 0), (4, 0), (4, 4), (0, 4), (0, 0)], [[(1, 1), (3, 1), (3, 3), (1, 3), (1, 1)]])
    assert polygon.equals(expected)

def test_gml_multipoint_to_shapely():
    gml_multipoint = """
    <MultiPoint xmlns="http://www.opengis.net/gml">
        <pointMember><Point><coordinates>1,2</coordinates></Point></pointMember>
        <pointMember><Point><coordinates>3,4</coordinates></Point></pointMember>
    </MultiPoint>
    """
    root = etree.fromstring(gml_multipoint)
    multipoint = GmlShapelyFactory.gml_multipoint_to_shapely(root)
    expected = MultiPoint([(1, 2), (3, 4)])
    assert multipoint.equals(expected)

def test_gml_multilinestring_to_shapely():
    gml_multilinestring = """
    <MultiLineString xmlns="http://www.opengis.net/gml">
        <lineStringMember><LineString><coordinates>0,0 1,1</coordinates></LineString></lineStringMember>
        <lineStringMember><LineString><coordinates>2,2 3,3</coordinates></LineString></lineStringMember>
    </MultiLineString>
    """
    root = etree.fromstring(gml_multilinestring)
    multilinestring = GmlShapelyFactory.gml_multilinestring_to_shapely(root)
    expected = MultiLineString([[(0, 0), (1, 1)], [(2, 2), (3, 3)]])
    assert multilinestring.equals(expected)

def test_gml_multipolygon_to_shapely():
    gml_multipolygon = """
    <MultiPolygon xmlns="http://www.opengis.net/gml">
        <polygonMember>
            <Polygon>
                <outerBoundaryIs><LinearRing><coordinates>0,0 1,0 1,1 0,1 0,0</coordinates></LinearRing></outerBoundaryIs>
            </Polygon>
        </polygonMember>
        <polygonMember>
            <Polygon>
                <outerBoundaryIs><LinearRing><coordinates>2,2 3,2 3,3 2,3 2,2</coordinates></LinearRing></outerBoundaryIs>
            </Polygon>
        </polygonMember>
    </MultiPolygon>
    """
    root = etree.fromstring(gml_multipolygon)
    multipolygon = GmlShapelyFactory.gml_multipolygon_to_shapely(root)
    expected = MultiPolygon([
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)])
    ])
    assert multipolygon.equals(expected)
