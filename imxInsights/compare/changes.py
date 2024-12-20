from dataclasses import dataclass
from enum import Enum
from typing import Any

from deepdiff import DeepDiff  # type: ignore
from shapely import LineString, Point

from imxInsights.compare.custom_operators.refs_diff_operator import UUIDListOperator
from imxInsights.compare.custom_operators.shapely_diff_operator import (
    ShapelyLineDiffer,
    ShapelyPointDiffer,
)
from imxInsights.compare.helpers import convert_deepdiff_path
from imxInsights.utils.flatten_unflatten import flatten_dict


class ChangeStatus(Enum):
    """
    Enum for representing different types of changes.
    """

    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    TYPE_CHANGE = "type_change"


@dataclass
class Change:
    """
    Dataclass for representing any type of change between two dictionaries.
    """

    status: ChangeStatus
    t1: Any | None = None
    t2: Any | None = None
    diff_string: str = ""
    analyse: Any | None = None


def process_deep_diff(dd: DeepDiff):
    changes = {}

    if "dictionary_item_added" in dd.keys():
        for key, value in dd["dictionary_item_added"].items():
            changes[convert_deepdiff_path(key)] = Change(
                status=ChangeStatus.ADDED,
                t1=None,
                t2=value,
                diff_string=f"++{value}",
                analyse=None,
            )

    if "dictionary_item_removed" in dd.keys():
        for key, value in dd["dictionary_item_removed"].items():
            if isinstance(value, dict):
                changes[convert_deepdiff_path(key)] = Change(
                    status=ChangeStatus.REMOVED,
                    t1=value,
                    t2=None,
                    diff_string=f"--{value}",
                    analyse=None,
                )
            else:
                raise NotImplementedError(f"{type(value)}")

    if "iterable_item_removed" in dd.keys():
        for key, value in dd["iterable_item_removed"].items():
            if isinstance(value, dict):
                for key_2, value_2 in value.items():
                    changes[f"{convert_deepdiff_path(key)}.{key_2}"] = Change(
                        status=ChangeStatus.REMOVED,
                        t1=value_2,
                        t2=None,
                        diff_string=f"--{value_2}",
                        analyse=None,
                    )
            else:
                raise NotImplementedError(f"{type(value)}")

    if "iterable_item_added" in dd.keys():
        for key, value in dd["iterable_item_added"].items():
            if isinstance(value, dict):
                for key_2, value_2 in value.items():
                    changes[f"{convert_deepdiff_path(key)}.{key_2}"] = Change(
                        status=ChangeStatus.ADDED,
                        t1=None,
                        t2=value_2,
                        diff_string=f"++{value_2}",
                        analyse=None,
                    )
            elif isinstance(value, str):
                changes[f"{convert_deepdiff_path(key)}.{key}"] = Change(
                    status=ChangeStatus.ADDED,
                    t1=None,
                    t2=value,
                    diff_string=f"++{value}",
                    analyse=None,
                )
            else:
                raise NotImplementedError(f"{type(value)}")

    if "type_changes" in dd.keys():
        for key, value in dd["type_changes"].items():
            if value["old_value"] is None:
                changes[convert_deepdiff_path(key)] = Change(
                    status=ChangeStatus.ADDED,
                    t1=None,
                    t2=value["new_value"],
                    diff_string=f"++{value['new_value']}",
                    # f"{value['old_value']} {value['old_type']} -> {value['new_value']} {value['new_type']}",
                    analyse=None,
                )

            elif value["new_value"] is None:
                changes[convert_deepdiff_path(key)] = Change(
                    status=ChangeStatus.REMOVED,
                    t1=value["old_value"],
                    t2=None,
                    diff_string=f"--{value['old_value']}",
                    # f"{value['old_value']} {value['old_type']} -> {value['new_value']} {value['new_type']}",
                    analyse=None,
                )

            else:
                changes[convert_deepdiff_path(key)] = Change(
                    status=ChangeStatus.TYPE_CHANGE,
                    t1=value["old_value"],
                    t2=value["new_value"],
                    diff_string=f"{value['old_value']} -> {value['new_value']}",
                    # f"{value['old_value']} {value['old_type']} -> {value['new_value']} {value['new_type']}",
                    analyse=None,
                )

    if "values_changed" in dd.keys():
        for key, value in dd["values_changed"].items():
            analyse = None
            if "diff_analyse" in dd.keys():
                if key in dd["diff_analyse"].keys():
                    analyse = dd["diff_analyse"][key]

            changes[convert_deepdiff_path(key)] = Change(
                status=ChangeStatus.CHANGED,
                t1=value["old_value"],
                t2=value["new_value"],
                diff_string=f"{value['old_value']} -> {value['new_value']}",
                analyse=analyse,
            )

    return changes


def get_object_changes(
    dict1: dict[str, Any], dict2: dict[str, Any]
) -> dict[str, Change]:
    """
    Compares two dictionaries and returns a dictionary that shows differences,
    unchanged values, and changes between them.

    Utilizes DeepDiff to perform the comparison and includes custom operators
    to handle specific types like UUIDs and Shapely objects.

    Args:
        dict1: The first dictionary to compare.
        dict2: The second dictionary to compare.

    Returns:
        A dictionary where keys represent the paths to changed elements,
        and values are `Change` objects describing the type of change.
    """

    # verbose should diff dicts in a list, make sure we set cutoff to 1
    dd = DeepDiff(
        dict1,
        dict2,
        ignore_order=True,
        verbose_level=2,
        cutoff_distance_for_pairs=1,
        cutoff_intersection_for_pairs=1,
        report_repetition=True,
        custom_operators=[
            UUIDListOperator(regex_paths=[r"root\['.*Refs'\]$"]),
            ShapelyPointDiffer(types=[Point]),
            ShapelyLineDiffer(types=[LineString]),
        ],
    )

    changes = process_deep_diff(dd)

    # we got the unchanged left
    flatten_dict_1 = flatten_dict(dict1)
    for key, value in flatten_dict_1.items():
        if key not in changes:
            changes[key] = Change(
                status=ChangeStatus.UNCHANGED,
                t1=value,
                t2=value,
                diff_string=f"{value}",
                analyse=None,
            )

    return changes
