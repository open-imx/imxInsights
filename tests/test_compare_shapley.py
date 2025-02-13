import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point, LineString

from imxInsights.compare.changes import process_deep_diff
from imxInsights.compare.custom_operators.diff_refs import UUIDListOperator
from imxInsights.compare.custom_operators.diff_shapely import ShapelyPointDiffer, ShapelyLineDiffer


def test_custom_differ():

    dict1 = {
        'Location.GeographicLocation.gml:Point.gml:coordinates': '182092.744,578919.029,1.043',
        'Location.GeographicLocation.gml:LineString.gml:coordinates': '181764.3,578840.086,1.206 181751.507,578837.585,1.206',
        'DivergingPassageRefs': '762f68cf-11c0-454a-8a51-c98e70c40675 224fe516-bf0d-4ef0-bc01-330e0828b25a 514169ce-81df-4100-b5b2-59a0639828a5',
    }
    dict2 = {
        'Location.GeographicLocation.gml:Point.gml:coordinates': '182092.744,578909.029,1.043',
        'Location.GeographicLocation.gml:LineString.gml:coordinates': '181764.3,578840.086,1.206 181752.507,578837.585,1.206 181752.507,578837.585,1',
        'DivergingPassageRefs': '224fe516-bf0d-4ef0-bc01-330e0828b25a 762f68cf-11c0-454a-8a51-c98e70c40675',
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
            # UUIDListOperator(regex_paths=[r"root\['.*Refs'\]$"]),
            ShapelyPointDiffer(regex_paths=[r"root\['.*gml:Point.gml:coordinates'\]$"]),
            ShapelyLineDiffer(
                regex_paths=[r"root\['.*gml:LineString.gml:coordinates'\]$"]
            ),
        ],
    )

    assert dd['diff_analyse']["root['Location.GeographicLocation.gml:Point.gml:coordinates']"] == {'display': 'almost_equal: False\nplanar distance: 10.0\nz_distance: no z', 'point_almost_equal': False, 'point_xy_distance': 10.0, 'point_z_distance': 'no z', 'type': 'ShapelyPointDiffer'}
    assert dd['diff_analyse']["root['Location.GeographicLocation.gml:LineString.gml:coordinates']"] == {'display': 'almost_equal: False\nintersection over union: 0.854\nplaner length difference: 0.98', 'intersection_over_union': 0.854, 'line_almost_equal': False, 'line_coordinate_difference': 1, 'line_max_z_distance': 0.206, 'line_planer_length_difference': 0.98, 'type': 'ShapelyLineDiffer'}
    # assert dd['diff_analyse']["root['DivergingPassageRefs']"] ==
