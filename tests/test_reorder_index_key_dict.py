import pytest

from imxInsights.utils.flatten_unflatten import reindex_dict


def test_reindex_dict_basic():
    data = {
        "group.1.name": "Alice",
        "group.2.name": "Bob",
        "group.3.name": "Charlie",
    }
    expected = {
        "group.0.name": "Alice",
        "group.1.name": "Bob",
        "group.2.name": "Charlie",
    }
    assert reindex_dict(data) == expected

def test_reindex_dict_mixed_keys():
    data = {
        "group.2.name": "Bob",
        "group.1.name": "Alice",
        "other.key": "value",
        "group.3.name": "Charlie",
    }
    expected = {
        "group.0.name": "Bob",
        "group.1.name": "Alice",
        "other.key": "value",
        "group.2.name": "Charlie",
    }
    assert reindex_dict(data) == expected

def test_reindex_dict_non_numeric():
    data = {
        "user.name": "Alice",
        "user.age": 30,
    }
    expected = {
        "user.name": "Alice",
        "user.age": 30,
    }
    assert reindex_dict(data) == expected

def test_reindex_dict_unordered_indices():
    data = {
        "group.5.name.0.test": "Eve",
        "group.3.name.0.test_2": "Charlie",
        "group.4.name.1.test": "David",
        "group.1.name": "Alice",
        "group.2.name": "Bob",
    }
    expected = {
        "group.0.name": "Eve",
        "group.1.name": "Charlie",
        "group.2.name": "David",
        "group.3.name": "Alice",
        "group.4.name": "Bob",
    }
    assert reindex_dict(data) == expected

