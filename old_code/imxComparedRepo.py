# import sys
# from collections import defaultdict
# from datetime import datetime
#
# import pandas as pd
# from loguru import logger
# from tqdm import tqdm
#
# from imxInsights.compare.changedImxObject import ChangedImxObject
# from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
# from imxInsights.utils.excel_helpers import shorten_sheet_name
# from imxInsights.utils.pandas_helpers import (
#     df_columns_sort_start_end,
#     styler_highlight_changes,
# )
#
#
# class ComparedMultiRepo:
#     def __init__(
#         self,
#         container_1: ImxContainerProtocol,
#         container_2: ImxContainerProtocol,
#         compared_objects: list[ChangedImxObject],
#     ):
#         self.container_1 = container_1
#         self.container_2 = container_2
#         self.compared_objects = []
#
#         with tqdm(total=len(compared_objects), file=sys.stdout) as pbar:  # type: ignore
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             pbar.set_description(
#                 f"{current_time} | {logger.level('INFO').name}     | Comparing objects"
#             )
#             for item in compared_objects:
#                 self.compared_objects.append(
#                     item.compare(container_1.container_id, container_2.container_id)
#                 )
#                 pbar.update(1)
#         logger.success("Compared all objects.")
#
#     def get_pandas_df(
#         self,
#         types: list[str] | None = None,
#         paths: list[str] | None = None,
#     ) -> pd.DataFrame:
#         imx_objects = self._filter_objects(types, paths)
#         return pd.DataFrame(imx_objects)
#
#     def _filter_objects(
#         self, types: list[str] | None, paths: list[str] | None
#     ) -> list[ChangedImxObject]:
#         def matches_criteria(obj: ChangedImxObject) -> bool:
#             if types:
#                 if (obj.t1 and obj.t1.tag in types) or (obj.t2 and obj.t2.tag in types):
#                     return True
#             if paths:
#                 if (obj.t1 and obj.t1.path in paths) or (
#                     obj.t2 and obj.t2.path in paths
#                 ):
#                     return True
#             return False
#
#         props_in_overview = [
#             "@puic",
#             "tag",
#             "path",
#             "@name",
#             "status",
#             "parent",
#             "children",
#             "Location.GeographicLocation.@accuracy",
#             "Location.GeographicLocation.@dataAcquisitionMethod",
#             "Metadata.@isInService",
#             "Metadata.@lifeCycleStatus",
#             "Metadata.@source",
#         ]
#
#         return (
#             [
#                 obj.get_change_dict(add_analyse=False)
#                 for obj in self.compared_objects
#                 if matches_criteria(obj)
#             ]
#             if types or paths
#             else [
#                 self._extract_overview_properties(_, props_in_overview)
#                 for _ in self.compared_objects
#             ]
#         )
#
#     @staticmethod
#     def _extract_overview_properties(item, input_props=None):
#         props = (
#             item.get_change_dict(add_analyse=False)
#             if input_props is None
#             else {
#                 key: value
#                 for key, value in item.get_change_dict(add_analyse=False).items()
#                 if key in input_props
#             }
#         )
#
#         return props
#
#     def get_dataframe_dict(self) -> dict[str, pd.DataFrame]:
#         def group_by_path(data_dict: list[dict]) -> dict[str, list[dict]]:
#             grouped = defaultdict(list)
#             for item in data_dict:
#                 path = item.get("path")
#                 path = path.lstrip("+-")
#                 grouped[path].append(item)
#             return dict(grouped)
#
#         start_columns = ["@puic", "path", "tag", "parent", "children", "status"]
#
#         data = group_by_path(
#             [_.get_change_dict(add_analyse=False) for _ in self.compared_objects]
#         )
#         _ = {}
#         status_order = ["added", "changed", "unchanged", "removed"]
#         for key, value in data.items():
#             _[key] = df_columns_sort_start_end(pd.DataFrame(value), start_columns, [])
#             _[key]["status"] = pd.Categorical(
#                 _[key]["status"], categories=status_order, ordered=True
#             )
#             _[key] = _[key].sort_values(by=["status", "@puic"])
#         return _
#
#     def get_excel(self, excel_file_path: str):
#         writer = pd.ExcelWriter(excel_file_path, engine="xlsxwriter")
#         index_sheet = writer.book.add_worksheet("index")
#         index_sheet.freeze_panes(1, 0)
#         index_sheet.write_string(0, 0, "path")
#         index_sheet.write_string(0, 1, "sheet name")
#         index_last_row = 1
#         sorted_dict = dict(sorted(self.get_dataframe_dict().items()))
#         for key, df in sorted_dict.items():
#             only_unchanged = (df["status"] == "unchanged").all()
#             sheet_name = shorten_sheet_name(key)
#             styled_df = df.style.map(styler_highlight_changes)
#
#             styled_df.to_excel(writer, sheet_name=sheet_name)
#             worksheet = writer.sheets[sheet_name]
#             worksheet.autofit()
#             worksheet.autofilter(0, 0, len(df), len(df.columns) - 1)
#             worksheet.freeze_panes(1, 0)
#             if only_unchanged:
#                 worksheet.tab_color = "gray"
#
#             index_sheet.write_string(index_last_row, 0, key)
#             index_sheet.write_url(
#                 index_last_row, 1, f"internal:{sheet_name}!A1", string=sheet_name
#             )
#
#             index_last_row += 1
#         index_sheet.autofit()
#         index_sheet.autofilter(0, 0, 0, 2)
#         writer.close()
