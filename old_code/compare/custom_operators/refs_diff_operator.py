# import re
# from typing import Any
#
# from deepdiff.operator import BaseOperator  # type: ignore
#
# UUIDv4_PATTERN = re.compile(
#     r"\b[0-9a-f]{8}-[0-9a-f]{4}-[4][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}\b"
# )
#
#
# class UUIDListOperator(BaseOperator):
#     """
#     Custom DeepDiff operator for comparing lists of UUIDs.
#     """
#
#     def __init__(self, regex_paths: list[str]):
#         """
#         Initialize UUIDListOperator with regex paths to match UUIDs.
#
#         Args:
#             regex_paths: List of regex paths to identify UUID fields.
#         """
#         super().__init__(regex_paths)
#
#     @staticmethod
#     def _create_display(
#         added_items: list[str], removed_items: list[str], unchanged_items: list[str]
#     ) -> list[str]:
#         added_items = [f"++{item}" for item in added_items]
#         removed_items = [f"--{item}" for item in removed_items]
#         return added_items + unchanged_items + removed_items
#
#     @staticmethod
#     def _split_uuids(uuid_str: str) -> list[str]:
#         return re.findall(UUIDv4_PATTERN, uuid_str)
#
#     def give_up_diffing(self, level: Any, diff_instance: Any) -> bool:
#         """
#         Compare two UUID lists and report differences in added, removed, and unchanged UUIDs.
#
#         Args:
#             level: The comparison level containing the two objects to compare.
#             diff_instance: The instance of DeepDiff that reports the differences.
#
#         Returns:
#             bool: True if a difference was found and reported.
#         """
#         if isinstance(level.t1, str) and isinstance(level.t2, str):
#             if UUIDv4_PATTERN.search(level.t1) and UUIDv4_PATTERN.search(level.t2):
#                 left_list = self._split_uuids(level.t1)
#                 right_list = self._split_uuids(level.t2)
#
#                 old_set = set(left_list)
#                 new_set = set(right_list)
#
#                 added_items = list(new_set - old_set)
#                 removed_items = list(old_set - new_set)
#                 unchanged_items = list(old_set & new_set)
#
#                 # Case when order of UUIDs changed but no items were added/removed
#                 if (len(added_items) == 0 or len(removed_items) == 0) and all(
#                     item in left_list for item in right_list
#                 ):
#                     diff_instance.custom_report_result(
#                         "diff_analyse",
#                         level,
#                         {
#                             "type": "UUIDListOperator",
#                             "added": added_items,
#                             "removed": removed_items,
#                             "unchanged": unchanged_items,
#                             "display": f"{left_list} -order_changed> {right_list} ",
#                             "status": "uuid_list_order_change",
#                         },
#                     )
#                     return True
#
#                 # Case when there are added or removed UUIDs
#                 elif len(added_items) > 0 or len(removed_items) > 0:
#                     diff_instance.custom_report_result("values_changed", level)
#
#                     status = (
#                         "uuid_list_only_added"
#                         if removed_items == []
#                         else "uuid_list_only_removed"
#                         if added_items == []
#                         else "uuid_list_changed"
#                     )
#
#                     diff_instance.custom_report_result(
#                         "diff_analyse",
#                         level,
#                         {
#                             "type": "UUIDListOperator",
#                             "added": added_items,
#                             "removed": removed_items,
#                             "unchanged": unchanged_items,
#                             "display": " ".join(
#                                 self._create_display(
#                                     added_items, removed_items, unchanged_items
#                                 )
#                             ),
#                             "status": status,
#                         },
#                     )
#
#                 else:
#                     diff_instance.custom_report_result(
#                         "values_unchanged", level, level.t1
#                     )
#
#                 return True
#         return False
