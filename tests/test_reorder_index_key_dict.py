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
        'group.3.name': 'Bob',
        'group.2.name': 'Alice',
        'group.1.name.0.test_1': 'Charlie',
        'group.1.name.1.test_2': 'David',
        'group.0.name.0.test': 'Eve',
    }
    expected = {
        'group.0.name': 'Bob',
        'group.1.name': 'Alice',
        'group.2.name.0.test_1': 'Charlie',
        'group.2.name.1.test_2': 'David',
        'group.3.name.0.test': 'Eve'}
    assert reindex_dict(data) == expected

