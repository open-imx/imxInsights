import pytest
from uuid import uuid4
from shapely.geometry import Point, LineString
from imxInsights.compare.changeStatusEnum import ChangeStatusEnum
from imxInsights.compare.changes import get_object_changes

def deepdiff_dicts(dict1, dict2):
    return get_object_changes(dict1, dict2)


def test_added_key():
    dict1 = {"a": 1}
    dict2 = {"a": 1, "b": 2}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["b"].status == ChangeStatusEnum.ADDED
    assert changes["b"].t1 is None
    assert changes["b"].t2 == 2


def test_removed_key():
    dict1 = {"a": 1, "b": 2}
    dict2 = {"a": 1}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["b"].status == ChangeStatusEnum.REMOVED
    assert changes["b"].t1 == 2
    assert changes["b"].t2 is None


def test_changed_value():
    dict1 = {"a": 1}
    dict2 = {"a": 2}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["a"].status == ChangeStatusEnum.CHANGED
    assert changes["a"].t1 == 1
    assert changes["a"].t2 == 2


def test_nested_added_key():
    dict1 = {"a": {"b": 1}}
    dict2 = {"a": {"b": 1, "c": 2}}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["a.b"].status == ChangeStatusEnum.UNCHANGED
    assert changes["a.c"].status == ChangeStatusEnum.ADDED
    assert changes["a.c"].t1 is None
    assert changes["a.c"].t2 == 2


def test_nested_removed_key():
    dict1 = {"a": {"b": 1, "c": 2}}
    dict2 = {"a": {"b": 1}}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["a.b"].status == ChangeStatusEnum.UNCHANGED
    assert changes["a.c"].status == ChangeStatusEnum.REMOVED
    assert changes["a.c"].t1 == 2
    assert changes["a.c"].t2 is None


def test_nested_changed_value():
    dict1 = {"a": {"b": 1}}
    dict2 = {"a": {"b": 2}}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["a.b"].status == ChangeStatusEnum.CHANGED
    assert changes["a.b"].t1 == 1
    assert changes["a.b"].t2 == 2


def test_type_change():
    dict1 = {"a": "1"}
    dict2 = {"a": 1}
    changes = deepdiff_dicts(dict1, dict2)
    assert changes["a"].status == ChangeStatusEnum.TYPE_CHANGE
    assert changes["a"].t1 == "1"
    assert changes["a"].t2 == 1


# # 3. List Changes
# def test_added_to_list():
#     # dict1 = {"a": [1, 2]}
#     # dict2 = {"a": [1, 2, 3]}
#     # changes = deepdiff_dicts(dict1, dict2)
#     # assert changes["a.2"].status == ChangeStatusEnum.ADDED
#     # assert changes["a.2"].t1 is None
#     # assert changes["a.2"].t2 == 3
#
#     dict1 = {"a": [1, 2]}
#     dict2 = {"a": [1, 3, 2]}
#     changes = deepdiff_dicts(dict1, dict2)
#     assert changes["a.0"].status == ChangeStatusEnum.UNCHANGED
#     assert changes["a.2"].t1 is None
#     assert changes["a.2"].t2 == 3
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


