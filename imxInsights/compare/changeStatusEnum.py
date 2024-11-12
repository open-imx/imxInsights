from enum import Enum


class ChangeStatusEnum(Enum):
    """
    Enum for representing different types of changes.
    """

    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    TYPE_CHANGE = "type_change"
