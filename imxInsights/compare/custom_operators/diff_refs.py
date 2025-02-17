import re
from typing import Any

from deepdiff.operator import BaseOperator  # type: ignore

# Regular expression for UUID v4
UUIDv4_PATTERN = re.compile(
    r"\b[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
)


class UUIDListOperator(BaseOperator):
    """
    Custom DeepDiff operator for comparing strings containing lists of UUIDs.
    """

    def __init__(self, regex_paths: list[str]):
        """
        Initialize with paths to match UUID fields.
        """
        super().__init__(regex_paths)

    @staticmethod
    def _create_display(
        added: list[str], removed: list[str], unchanged: list[str]
    ) -> list[str]:
        """
        Create a display list where added UUIDs are prefixed with '++'
        and removed UUIDs with '--'. Unchanged UUIDs remain unmodified.
        """
        display_added = [f"++{item}" for item in added]
        display_removed = [f"--{item}" for item in removed]
        return display_added + unchanged + display_removed

    @staticmethod
    def _split_uuids(uuid_str: str) -> list[str]:
        """
        Extract UUIDs from the input string using the UUIDv4_PATTERN.
        """
        return re.findall(UUIDv4_PATTERN, uuid_str)

    def give_up_diffing(self, level: Any, diff_instance: Any) -> bool:
        """
        Compare two UUID strings (level.t1 and level.t2) and report:
          - Order changes (same set of UUIDs, but different order)
          - Genuine additions or removals of UUIDs.

        Returns True if the difference has been reported.
        """
        # Ensure both items are strings containing UUIDs
        if not (isinstance(level.t1, str) and isinstance(level.t2, str)):
            return False
        if not (UUIDv4_PATTERN.search(level.t1) and UUIDv4_PATTERN.search(level.t2)):
            return False
        elif level.t1 == level.t2:
            return True

        # Extract UUIDs from both strings
        old_uuids = self._split_uuids(level.t1)
        new_uuids = self._split_uuids(level.t2)

        # Use sets to identify differences regardless of order
        old_set, new_set = set(old_uuids), set(new_uuids)
        added = list(new_set - old_set)
        removed = list(old_set - new_set)
        unchanged = list(old_set & new_set)

        # Case 1: The two lists have the same UUIDs, so any difference is just order.
        if not added and not removed:
            if old_uuids != new_uuids:
                diff_instance.custom_report_result("values_changed", level)

                diff_instance.custom_report_result(
                    "diff_analyse",
                    level,
                    {
                        "type": "UUIDListOperator",
                        "added": [],
                        "removed": [],
                        "unchanged": unchanged,
                        "display": "order_changed",
                        "status": "uuid_list_order_change",
                    },
                )
            else:
                # No differences at all
                diff_instance.custom_report_result("values_unchanged", level, level.t1)
            return True

        # Case 2: There are genuine additions and/or removals.
        diff_instance.custom_report_result("values_changed", level)

        # Determine the status based on the differences
        if not removed:
            status = "uuid_list_only_added"
        elif not added:
            status = "uuid_list_only_removed"
        else:
            status = "uuid_list_changed"

        display = " ".join(self._create_display(added, removed, unchanged))
        diff_instance.custom_report_result(
            "diff_analyse",
            level,
            {
                "type": "UUIDListOperator",
                "added": added,
                "removed": removed,
                "unchanged": unchanged,
                "display": display,
                "status": status,
            },
        )
        return True
