# from datetime import datetime
# from pathlib import Path
#
# import pandas as pd
# from loguru import logger
#
# from imxInsights.file.singleFileImx.imxSituation import ImxSituation
# from imxInsights.report.commen import create_container_imx_info, create_single_imx_info
# from imxInsights.report.excelGenerator import ExcelReportGenerator
# from imxInsights.utils.flatten_unflatten import hash_sha256
#
#
# def create_metadata_info_sheet():
#     additional_info = {
#         "Create date": datetime.now().strftime("%Y-%m-%d"),
#     }
#     return pd.DataFrame(list(additional_info.items()), columns=["Key", "Value"])
#
#
# class ExcelImxDiffReport(ExcelReportGenerator):
#     def __init__(
#         self,
#         pandas_df_dict: dict[str, pd.DataFrame],
#         containers: list[ImxSituation],
#         container_order: tuple[str, ...],
#         file_path: str | Path,
#     ):
#         super().__init__(file_path)
#         self.pandas_df_dict: dict[str, pd.DataFrame] = pandas_df_dict
#         self.containers: list[ImxSituation] = containers
#         self.container_order: tuple[str, ...] = container_order
#
#     def _create_info_sheet(self):
#         sheet_name = "Info"
#         empty_row = 0
#         self.add_dataframe(
#             create_metadata_info_sheet(), sheet_name, startrow=empty_row, startcol=1
#         )
#         empty_row = +1
#
#         self.add_list_of_lists(
#             [["ImxInsights version", "v0.2.0-alpha"]],
#             sheet_name,
#             startrow=empty_row,
#             startcol=1,
#         )
#         empty_row += 2
#
#         self.add_list_of_lists(
#             [["container_order"]], sheet_name, startrow=empty_row, startcol=1
#         )
#         empty_row += 1
#
#         self.add_list_of_lists(
#             [[f"T{idx}", _] for idx, _ in enumerate(self.container_order, start=1)],
#             sheet_name,
#             startrow=empty_row,
#             startcol=1,
#         )
#         empty_row += len(self.container_order) + 1
#
#         # process container info....
#         for idx, container_id in enumerate(self.container_order, start=1):
#             for container in self.containers:
#                 if container.container_id == container_id:
#                     if int(container.imx_version.split(".")[0]) >= 12:
#                         self.add_dataframe(
#                             create_container_imx_info(
#                                 container.container_id,
#                                 f"{container.path.name}",
#                                 "todo: make 12 methode",
#                                 container.imx_version,
#                                 prefix=f"T{idx}_",
#                             ),
#                             sheet_name,
#                             startrow=empty_row,
#                             startcol=1,
#                         )
#                         empty_row = empty_row + 6
#                     else:
#                         self.add_dataframe(
#                             create_single_imx_info(
#                                 container_id=container.container_id,
#                                 file_path=f"{container.path}",
#                                 situation_type=container.situation_type.name,
#                                 calculated_file_hash=hash_sha256(self.file_path),
#                                 imx_version=container.imx_version,
#                                 prefix=f"T{idx}_",
#                             ),
#                             sheet_name,
#                             startrow=empty_row,
#                             startcol=1,
#                         )
#                         empty_row = empty_row + 6
#                     break
#
#         self.auto_fit_columns(sheet_name)
#
#     @staticmethod
#     def create_excel(
#         pandas_df_dict: dict[str, pd.DataFrame],
#         containers: list[ImxSituation],
#         container_order: tuple[str, ...],
#         file_path: str
#         | Path = f'diff_excel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
#         add_log: bool = False,
#     ):
#         self = ExcelImxDiffReport(
#             pandas_df_dict, containers, container_order, file_path
#         )
#         self._create_info_sheet()
#
#         self._create_diff_sheets()
#
#         if add_log:
#             self.log_history()
#         self.save()
#
#     def _create_diff_sheets(self):
#         pass
#
#
# # ExcelImxDiffReport.create_excel("tester.xlsx", add_log=True)
# #
