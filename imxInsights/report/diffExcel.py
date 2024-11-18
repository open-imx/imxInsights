# from __future__ import annotations
#
# # import importlib.metadata
# import sys
# import uuid
# from datetime import datetime
# from pathlib import Path
# from typing import TYPE_CHECKING
#
# import pandas as pd
# from loguru import logger
# from tqdm import tqdm
#
# from imxInsights.report.excelGenerator import ExcelReport
# from imxInsights.utils.excel_helpers import shorten_sheet_name
#
# if TYPE_CHECKING:
#     from imxInsights.compare.changedImxObject import ChangedImxObject
#     from imxInsights.compare.compareMultiRepo import ImxCompareMultiRepo
#
#
# class DiffExcel(ExcelReport):
#     def __init__(
#         self,
#         imx_multi_container: ImxCompareMultiRepo,
#         file_path: str | Path,
#         styled_df: bool = False,
#         add_analyse: bool = False,
#     ):
#         super().__init__(file_path)
#         self.repo = imx_multi_container
#         self.diff_df_dict = imx_multi_container.get_pandas(
#             styled_df=styled_df, add_analyse=add_analyse
#         )
#         self.container_order = imx_multi_container.container_order
#         self._containers = imx_multi_container._containers
#
#         self.create_info_sheet()
#         self.index_sheet = self.get_or_create_worksheet("index")
#         self.index_sheet_last_row = 0
#         self.create_metadata_overview()
#         self.create_object_sheets()
#
#         self.auto_fit_columns()
#
#     def create_info_sheet(self):
#         next_row = self.add_list_of_lists(
#             [
#                 ["IMX diff Excel"],
#                 # [f"ImxInsights ({importlib.metadata.version("imxInsights")})"],
#                 ["https://open-imx.nl/"],
#             ],
#             sheet_name="info",
#             start_row=1,
#             start_col=1,
#             header=False,
#             index=False,
#             cell_format="h1",
#             cell_format_range=[1, 1, 1, 1],
#         )
#         self.format_row("info", 2, "h3")
#
#         cell_hover = {  # for row hover use <tr> instead of <td>
#             "selector": "td:hover",
#             "props": [("background-color", "#ffffb3")],
#         }
#
#         # below, does not set the to_excel format :/
#         index = {  # for row hover use <tr> instead of <td>
#             "selector": "th",
#             "props": [
#                 ("background-color", "#000066"),
#                 ("color", "green"),
#                 ("text-align", "left"),
#             ],
#         }
#
#         sorted_objects = sorted(
#             self._containers,
#             key=lambda obj: self.container_order.index(obj.container_id)
#             if obj.container_id in self.container_order
#             else float("inf"),
#         )
#
#         for idx, item in enumerate(sorted_objects, start=1):
#             self.write_cell("info", next_row + 1, 1, f"IMX T{idx}", "h2")
#             imx_info_df = item.dataframes.combined_info_df(pivot_df=True)
#
#             styled_imx_info_df = imx_info_df.style.set_properties(
#                 subset=None, **{"background-color": "#ECE3FF", "color": "black"}
#             ).map(lambda x: "border: 1px solid;")  # type: ignore
#             styled_imx_info_df = styled_imx_info_df.set_table_styles(
#                 [cell_hover, index]
#             )
#
#             next_row = self.add_dataframe(
#                 styled_imx_info_df,
#                 "info",
#                 start_row=next_row + 2,
#                 start_col=1,
#                 header=False,
#             )
#
#     def _get_full_path(self, node):
#         path: list[list[str]] = []
#         current = node
#         while current:
#             path.insert(0, current.path)
#             path.insert(1, current.puic)
#             current = current.parent
#         return path
#
#     @staticmethod
#     def is_uuid(s):
#         try:
#             uuid.UUID(s)
#             return True  # NOQA TRY300
#         except ValueError as e:  # NOQA F841
#             return False
#
#     def create_metadata_overview(self):
#         # TODO: Getting the df should be in the compair object.
#         nodes = []
#         for container in self._containers:
#             nodes.append(list(container.get_all()))
#
#         paths_a = [self._get_full_path(node) for node in nodes[0]]
#         paths_b = [self._get_full_path(node) for node in nodes[1]]
#
#         puics_in_a = [_[-1] for _ in paths_a]
#         for item in paths_b:
#             if item[-1] not in puics_in_a:
#                 paths_a.append(item)
#
#         list_of_columns = [
#             "@name",
#             "status",
#             "Metadata.@isInService",
#             "Metadata.@lifeCycleStatus",
#             "Metadata.@originType",
#             "Metadata.@registrationTime",
#             "Metadata.@source",
#         ]
#         # TODO: below will break we object type is not present in t2 container, should be fixed in refactor :-)
#         status_list = [
#             [item2 for item2 in self.repo.diff[item[-2]] if item2.puic == item[-1]][0]
#             for item in paths_a
#         ]
#         status: dict[str, ChangedImxObject] = {item.puic: item for item in status_list}
#
#         for item in paths_a:
#             item.insert(len(item) - 1, f"_{status[item[-1]].status.name}")
#
#         paths_a.sort(key=lambda x: tuple(x))
#
#         properties = []
#         for item in paths_a:
#             uuids = [s for s in item if self.is_uuid(s)]
#             puic = uuids[-1] if len(uuids) >= 1 else None
#             change_obj = status[f"{puic}"]
#             props = {
#                 key: change_obj.changes[key].diff_string
#                 for key in list_of_columns
#                 if key in change_obj.changes
#             }
#             properties.append(
#                 {"@puic": f"{puic}", "change_status": change_obj.status.name} | props
#             )
#
#         df = pd.DataFrame(properties)
#
#         max_depth = max(len(path) for path in paths_a)
#         index = pd.MultiIndex.from_tuples(
#             paths_a, names=[f"Level{i + 1}" for i in range(max_depth)]
#         )
#         df.index = index
#
#         # df = df.reset_index()
#         # df = df.groupby(level=f'Level{max_depth}', group_keys=False).apply(lambda x: x.sort_values(by='change_status', ascending=False))
#
#         def highlight_borders(row):
#             if row["change_status"] == "ADDED":
#                 return [
#                     "background-color: #ff9999; font-weight: bold; color: black;"
#                 ] * len(row)  # Brighter light red
#             elif row["change_status"] == "REMOVED":
#                 return [
#                     "background-color: #99ccff; font-weight: bold; color: black;"
#                 ] * len(row)  # Brighter light blue
#             elif row["change_status"] == "CHANGED":
#                 return [
#                     "background-color: #d4edda; font-weight: bold; color: black;"
#                 ] * len(row)  # Light green
#             elif row["change_status"] == "UNCHANGED":
#                 return [
#                     "background-color: #f0f0f0; font-weight: normal; color: black;"
#                 ] * len(row)  # Light gray
#             else:
#                 return [""] * len(row)
#
#         # Apply the styling based on 'change_status'
#         df = df.style.apply(highlight_borders, axis=1)  # type: ignore
#
#         self.add_dataframe(
#             df,
#             "meta_overview",
#             start_row=0,
#             start_col=1,
#             header=True,
#         )
#         for indx in range(0, max_depth + 1):
#             if indx & 1 != 1 and indx != 0:
#                 self.format_column(
#                     "meta_overview", indx, indx, {}, None, {"level": 1, "hidden": True}
#                 )
#
#     def create_object_sheets(self):
#         with tqdm(total=len(self.diff_df_dict.keys()), file=sys.stdout) as pbar:  # type: ignore
#             current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
#             pbar.set_description(
#                 f"{current_time} | {logger.level('INFO').name}     | Writing Excel Sheet"
#             )
#             for key, imx_object_df in self.diff_df_dict.items():
#                 sheet_name = shorten_sheet_name(f"{key}")
#
#                 self.index_sheet.write(self.index_sheet_last_row, 0, key)
#                 self.index_sheet.write_url(
#                     self.index_sheet_last_row,
#                     1,
#                     f"internal:{sheet_name}!A1",
#                     string=sheet_name,
#                 )
#                 self.index_sheet_last_row = self.index_sheet_last_row + 1
#
#                 if not isinstance(imx_object_df, dict):
#                     next_row = self.add_dataframe(
#                         imx_object_df,  # type: ignore
#                         sheet_name,
#                         start_row=0,
#                         start_col=0,
#                         header=True,
#                     )
#                     worksheet = self.get_or_create_worksheet(sheet_name)
#                     worksheet.freeze_panes(1, 0)
#                     worksheet.autofilter(0, 0, 0, next_row)
#
#                     if (imx_object_df.data["status"] == "unchanged").all():
#                         worksheet.set_tab_color("gray")
#
#                 pbar.update(1)
