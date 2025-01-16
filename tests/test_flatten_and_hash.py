from pathlib import Path
from typing import Any

import pytest

from imxInsights.utils.flatten_unflatten import flatten_dict, parse_to_nested_dict
from imxInsights.utils.hash import hash_dict_ignor_nested, hash_sha256


def test_hash_sha256_valid_file(tmp_path):
    file = tmp_path / "test_file.txt"
    file.write_text("Hello, world!")
    expected_hash = "315f5bdb76d078c43b8ac0064e4a0164612b1fce77c869345bfc94c75894edd3"
    assert hash_sha256(file) == expected_hash


def test_hash_sha256_file_not_found():
    non_existent_file = Path("non_existent_file.txt")
    with pytest.raises(ValueError, match="FileNotFoundError: File not found"):
        hash_sha256(non_existent_file)


def test_hash_dict_ignor_nested():
    test_dict = {
        "key1": "value1",
        "key2": {"nested_key": "nested_value"},
        "key3": "value3",
    }
    expected_hash = "12faf4ed6739d9d9b8f134624f4b2c1c4372ba79"  # Precomputed SHA-1 hash
    assert hash_dict_ignor_nested(test_dict) == expected_hash


def test_flatten_dict_basic():
    test_dict: dict[str, str | dict[str, Any] | list] = {
        "key1": "value1",
        "key2": {"nested_key1": "nested_value1", "nested_key2": "nested_value2"},
        "key3": ["item1", "item2"],  # This is a list, which is expected
    }
    expected_flattened = {
        "key1": "value1",
        "key2.nested_key1": "nested_value1",
        "key2.nested_key2": "nested_value2",
        "key3.0": "item1",
        "key3.1": "item2",
    }
    assert flatten_dict(test_dict) == expected_flattened


def test_flatten_dict_with_skip_key():
    test_dict: dict[str, str | dict[str, Any] | list] = {
        "key1": "value1",
        "@puic": "skip_this",
        "key2": {"nested_key1": "nested_value1"},
    }
    expected_flattened = {
        "@puic": "skip_this",
        "key1": "value1",
        "key2.nested_key1": "nested_value1",
    }
    assert flatten_dict(test_dict, skip_key="@puic") == expected_flattened


def test_parse_to_nested_dict():
    test_dict = {
        "key1": "value1",
        "key2.nested_key1": "nested_value1",
        "key2.nested_key2": "nested_value2",
    }
    expected_parsed = {
        "key1": "value1",
        "key2": {"nested_key1": "nested_value1", "nested_key2": "nested_value2"},
    }
    assert parse_to_nested_dict(test_dict) == expected_parsed


def test_parse_to_nested_dict_with_numbers_in_key():
    test_dict = {
        "key1": "value1",
        "key2.0": "value2",
        "key2.1.nested_key": "nested_value",
    }
    expected_parsed = {
        "key1": "value1",
        "key2": {"0": "value2", "1": {"nested_key": "nested_value"}},
    }
    assert parse_to_nested_dict(test_dict) == expected_parsed
