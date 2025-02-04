# import pytest
# from uuid import uuid4
# from shapely.geometry import Point, LineString
# from imxInsights.compare.changeStatusEnum import ChangeStatusEnum
# from imxInsights.compare.changes import get_object_changes
# from imxInsights.compare.helpers import convert_deepdiff_path
#
# # Helper function to compare two dictionaries using DeepDiff
# def deepdiff_dicts(dict1, dict2):
#     return get_object_changes(dict1, dict2)
#
#
# # 1. Simple Dictionary Changes
# def test_added_key():
#     dict1 = {"a": 1}
#     dict2 = {"a": 1, "b": 2}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["b"].status == ChangeStatusEnum.ADDED
#     assert changes["b"].t1 is None
#     assert changes["b"].t2 == 2
#
#
# def test_removed_key():
#     dict1 = {"a": 1, "b": 2}
#     dict2 = {"a": 1}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["b"].status == ChangeStatusEnum.REMOVED
#     assert changes["b"].t1 == 2
#     assert changes["b"].t2 is None
#
#
# def test_changed_value():
#     dict1 = {"a": 1}
#     dict2 = {"a": 2}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"].status == ChangeStatusEnum.CHANGED
#     assert changes["a"].t1 == 1
#     assert changes["a"].t2 == 2
#
#
# # 2. Nested Dictionary Changes
# def test_nested_added_key():
#     dict1 = {"a": {"b": 1}}
#     dict2 = {"a": {"b": 1, "c": 2}}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"]["c"].status == ChangeStatusEnum.ADDED
#     assert changes["a"]["c"].t1 is None
#     assert changes["a"]["c"].t2 == 2
#
#
# def test_nested_removed_key():
#     dict1 = {"a": {"b": 1, "c": 2}}
#     dict2 = {"a": {"b": 1}}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"]["c"].status == ChangeStatusEnum.REMOVED
#     assert changes["a"]["c"].t1 == 2
#     assert changes["a"]["c"].t2 is None
#
#
# def test_nested_changed_value():
#     dict1 = {"a": {"b": 1}}
#     dict2 = {"a": {"b": 2}}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"]["b"].status == ChangeStatusEnum.CHANGED
#     assert changes["a"]["b"].t1 == 1
#     assert changes["a"]["b"].t2 == 2
#
#
# # 3. List Changes
# def test_added_to_list():
#     dict1 = {"a": [1, 2]}
#     dict2 = {"a": [1, 2, 3]}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"][2].status == ChangeStatusEnum.ADDED
#     assert changes["a"][2].t1 is None
#     assert changes["a"][2].t2 == 3
#
#
# def test_removed_from_list():
#     dict1 = {"a": [1, 2, 3]}
#     dict2 = {"a": [1, 2]}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"][2].status == ChangeStatusEnum.REMOVED
#     assert changes["a"][2].t1 == 3
#     assert changes["a"][2].t2 is None
#
#
# def test_changed_in_list():
#     dict1 = {"a": [1, 2, 3]}
#     dict2 = {"a": [1, 2, 4]}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"][2].status == ChangeStatusEnum.CHANGED
#     assert changes["a"][2].t1 == 3
#     assert changes["a"][2].t2 == 4
#
#
# # 4. Type Changes
# def test_type_change():
#     dict1 = {"a": "1"}
#     dict2 = {"a": 1}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"].status == ChangeStatusEnum.TYPE_CHANGE
#     assert changes["a"].t1 == "1"
#     assert changes["a"].t2 == 1
#
#
# # 5. UUID Changes (If applicable)
# def test_uuid_change():
#     dict1 = {"refs": [str(uuid4())]}
#     dict2 = {"refs": [str(uuid4())]}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["refs"][0].status == ChangeStatusEnum.CHANGED
#
#
# # 6. Shapely Geometry Changes
# def test_shapely_point_change():
#     point1 = Point(1, 1)
#     point2 = Point(2, 2)
#     dict1 = {"a": point1}
#     dict2 = {"a": point2}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"].status == ChangeStatusEnum.CHANGED
#     assert changes["a"].t1 == point1
#     assert changes["a"].t2 == point2
#
#
# def test_shapely_line_change():
#     line1 = LineString([(0, 0), (1, 1)])
#     line2 = LineString([(1, 1), (2, 2)])
#     dict1 = {"a": line1}
#     dict2 = {"a": line2}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a"].status == ChangeStatusEnum.CHANGED
#     assert changes["a"].t1 == line1
#     assert changes["a"].t2 == line2
