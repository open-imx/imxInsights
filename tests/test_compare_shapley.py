import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point, LineString

from imxInsights.compare.changes import process_deep_diff
from imxInsights.compare.custom_operators.diff_shapely import ShapelyPointDiffer, ShapelyLineDiffer


@pytest.fixture
def sample_points():
    return Point(1, 1), Point(2, 2)


@pytest.fixture
def sample_lines():
    return LineString([(0, 0), (1, 1), (2, 2)]), LineString([(0, 0), (1, 1), (3, 3)])


@pytest.fixture
def sample_dicts(sample_points, sample_lines):
    p1, p2 = sample_points
    l1, l2 = sample_lines
    return {"point": p1, "line": l1}, {"point": p2, "line": l2}


def test_shapely_differ(sample_dicts):

    # basic point and line
    dict1 = {
        "line":  LineString([(0, 0), (1, 1), (2, 2)]),
        "point": Point(1, 1)
    }
    dict2 = {
        "line": LineString([(0, 0), (1, 1), (3, 3)]),
        "point": Point(2, 2)
    }

    dd = DeepDiff(
        dict1,
        dict2,
        ignore_order=True,
        verbose_level=2,
        cutoff_distance_for_pairs=1,
        cutoff_intersection_for_pairs=1,
        report_repetition=True,
        custom_operators=[
            ShapelyPointDiffer(types=[Point]),
            ShapelyLineDiffer(types=[LineString]),
        ],
    )
    assert dd['diff_analyse']["root['point']"] == {'display': 'almost_equal: False\nplanar distance: 1.414\nz_distance: no z', 'point_almost_equal': False, 'point_xy_distance': 1.414, 'point_z_distance': 'no z', 'type': 'ShapelyPointDiffer'}
    assert dd['diff_analyse']["root['line']"] == {'display': 'almost_equal: False\nintersection over union: 0.757\nplaner length difference: 1.414', 'intersection_over_union': 0.757, 'line_almost_equal': False, 'line_coordinate_difference': 0, 'line_max_z_distance': 'no z', 'line_planer_length_difference': 1.414, 'type': 'ShapelyLineDiffer'}

    dict1 = {
        "point_0": Point(1, 1),
        "point_1": Point(1, 1, 1),
        "point_2": Point(1, 1, 2)
    }
    dict2 = {
        "point_0": Point(1, 1, 1),
        "point_1": Point(2, 2),
        "point_2": Point(2, 2, 3)
    }
    dd = DeepDiff(
        dict1,
        dict2,
        ignore_order=True,
        verbose_level=2,
        cutoff_distance_for_pairs=1,
        cutoff_intersection_for_pairs=1,
        report_repetition=True,
        custom_operators=[
            ShapelyPointDiffer(types=[Point]),
            ShapelyLineDiffer(types=[LineString]),
        ],
    )
    assert dd['diff_analyse']["root['point_0']"]['point_z_distance'] == 'added'
    assert dd['diff_analyse']["root['point_1']"]['point_z_distance'] == 'removed'
    assert dd['diff_analyse']["root['point_2']"]['point_z_distance'] == 1.0

    # change in coordinate length
    # z changed



    dict1 = {
        "line_0": LineString([(0, 0), (1, 1), (2, 2)]),
        "line_1": LineString([(0, 0, 0), (1, 1, 0), (2, 2, 0)]),
        "line_2": LineString([(0, 0), (1, 1), (2, 2)]),
        "line_3": LineString([(0, 0, 1), (1, 1, 1), (2, 2, 1)]),
    }
    dict2 = {
        "line_0": LineString([(0, 0), (0.5, 0.5), (1, 1), (2, 2)]),
        "line_1": LineString([(0, 0, 0), (1, 1, 2), (2, 2, 0)]),
        "line_2": LineString([(0, 0, 1), (1, 1, 1), (2, 2, 1)]),
        "line_3": LineString([(0, 0), (1, 1), (2, 2)]),
    }
    dd = DeepDiff(
        dict1,
        dict2,
        ignore_order=True,
        verbose_level=2,
        cutoff_distance_for_pairs=1,
        cutoff_intersection_for_pairs=1,
        report_repetition=True,
        custom_operators=[
            ShapelyPointDiffer(types=[Point]),
            ShapelyLineDiffer(types=[LineString]),
        ],
    )

    assert dd['diff_analyse']["root['line_0']"]['line_coordinate_difference'] == 1.0
    assert dd['diff_analyse']["root['line_1']"]['line_max_z_distance'] == 2.0
    assert dd['diff_analyse']["root['line_2']"]['line_max_z_distance'] == 'added'
    assert dd['diff_analyse']["root['line_3']"]['line_max_z_distance'] == 'removed'

