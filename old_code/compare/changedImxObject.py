# from dataclasses import dataclass
#
# from imxInsights.compare.changes import Change, ChangeStatus
# from imxInsights.compare.geometryChange import GeometryChange
#
#
# @dataclass
# class ChangedImxObject:
#     """
#     Represents a changed IMX object with its change status and details.
#
#     Attributes:
#         puic (str): The unique identifier of the IMX object.
#         status (ChangeStatus): The change status of the IMX object.
#         changes (dict[str, Change]): A dictionary of changes for the IMX object.
#     """
#
#     puic: str
#     status: ChangeStatus
#     changes: dict[str, Change]
#     geometry: GeometryChange | None
#
#     def get_change_dict(self, add_analyse: bool) -> dict[str, str]:
#         """
#         Get a dictionary representation of the changes.
#
#         Args:
#             add_analyse (bool): Whether to include the analyse details in the result.
#
#         Returns:
#             A dictionary with change details and status.
#         """
#         analyse = (
#             {
#                 f"{key}_analyse": value.analyse["display"]
#                 for key, value in self.changes.items()
#                 if value.analyse is not None
#             }
#             if add_analyse
#             else {}
#         )
#
#         return (
#             {key: value.diff_string for key, value in self.changes.items()}
#             | analyse
#             | {"status": self.status.value}
#         )
