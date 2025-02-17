import numpy as np
import pytest
from deepdiff import DeepDiff
from shapely.geometry import Point, LineString

from imxInsights.compare.changes import process_deep_diff
from imxInsights.compare.custom_operators.diff_refs import UUIDListOperator
from imxInsights.compare.custom_operators.diff_shapely import ShapelyPointDiffer, ShapelyLineDiffer


def test_custom_differ():
    dict1 = {
        'Location.GeographicLocation.gml:Point.gml:coordinates': '183836.446,568138.764,3.141',
        'Location.GeographicLocation.gml:LineString.gml:coordinates': '181764.3,578840.082,1.202 181751.507,578837.585,1.206',
        'DivergingPassageRefs': '762f68cf-11c0-454a-8a51-c98e70c40675 224fe516-bf0d-4ef0-bc01-330e0828b25a 514169ce-81df-4100-b5b2-59a0639828a5',
    }
    dict2 = {
        'Location.GeographicLocation.gml:Point.gml:coordinates': '183836.446,568138.764,3.142',
        'Location.GeographicLocation.gml:LineString.gml:coordinates': '181764.3,578840.082,1.206 181751.507,578837.585,1.206',
        'DivergingPassageRefs': '762f68cf-11c0-454a-8a51-c98e70c40675 514169ce-81df-4100-b5b2-59a0639828a5 224fe516-bf0d-4ef0-bc01-330e0828b25a',
    }

    dd = DeepDiff(
        dict2,
        dict1,
        ignore_order=True,
        verbose_level=2,
        cutoff_distance_for_pairs=1,
        cutoff_intersection_for_pairs=1,
        report_repetition=True,
        custom_operators=[
            UUIDListOperator(regex_paths=[r"root\['.*Refs'\]$"]),
            ShapelyPointDiffer(regex_paths=[r"root\['.*gml:Point.gml:coordinates'\]$"]),
            ShapelyLineDiffer(
                regex_paths=[r"root\['.*gml:LineString.gml:coordinates'\]$"]
            ),
        ],
    )

    assert "root['Location.GeographicLocation.gml:Point.gml:coordinates']" in dd['diff_analyse'].keys()
    assert "root['Location.GeographicLocation.gml:LineString.gml:coordinates']" in dd['diff_analyse'].keys()
    assert "root['DivergingPassageRefs']" in dd['diff_analyse'].keys()
