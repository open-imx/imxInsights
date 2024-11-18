# import shutil
# import tempfile
# from pathlib import Path
#
# import pandas as pd
# from loguru import logger
# from pandas.io.formats.style import Styler
#
#
# class ExcelReport:
#     def __init__(self, file_path: str | Path):
#         self.file_path = file_path
#         self.temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
#         self.writer = pd.ExcelWriter(self.temp_file.name, engine="xlsxwriter")
#         self.workbook = self.writer.book
#         self.formats = self._initialize_formats()
#
#     @staticmethod
#     def _initialize_formats():
#         return {
#             "h1": {"bold": True, "font_size": 24, "align": "left"},
#             "h2": {"bold": True, "font_size": 18, "align": "left"},
#             "h3": {"bold": True, "font_size": 14, "align": "left"},
#             "bold": {"bold": True},
#             "italic": {"italic": True},
#             "bold_italic": {"bold": True, "italic": True},
#             "border": {"border": 1},
#             "left": {"bold": True, "font_size": 20, "align": "left"},
#             "center": {"align": "center"},
#         }
#
#     def get_all_format_types(self):
#         return self.formats.keys()
#
#     def get_format(self, key: str | list[str]):
#         if isinstance(key, list):
#             self._validate_format_keys(key)
#             return {k: v for d in [self.formats[_] for _ in key] for k, v in d.items()}
#         return self._get_single_format(key)
#
#     def _validate_format_keys(self, keys: list[str]):
#         for key in keys:
#             if key not in self.formats:
#                 raise ValueError(f"No format matches '{key}'")  # NOQA TRY003
#
#     def _get_single_format(self, key: str):
#         if key not in self.formats:
#             raise ValueError(f"No format matches '{key}'")  # NOQA TRY003
#         return self.formats[key]
#
#     def add_dataframe(
#         self,
#         df: pd.DataFrame,
#         sheet_name: str,
#         start_row: int = 0,
#         start_col: int = 0,
#         index: bool = True,
#         header: bool = True,
#     ):
#         df.to_excel(
#             self.writer,
#             sheet_name=sheet_name,
#             index=index,
#             header=header,
#             startrow=start_row,
#             startcol=start_col,
#         )
#         return (
#             len(df) + start_row
#             if not isinstance(df, Styler)
#             else len(df.data) + start_row
#         )
#
#     def add_list_of_lists(
#         self,
#         data: list[list],
#         sheet_name: str,
#         start_row: int = 0,
#         start_col: int = 0,
#         header: bool = True,
#         index: bool = True,
#         cell_format: str | None = None,
#         cell_format_range: list[int] | None = None,
#     ):
#         if not cell_format:
#             df = pd.DataFrame(data)
#             return self.add_dataframe(
#                 df, sheet_name, start_row, start_col, header, index
#             )
#
#         self._write_list_with_format(
#             data, sheet_name, start_row, start_col, cell_format, cell_format_range
#         )
#         return len(data) + start_row
#
#     def _write_list_with_format(
#         self,
#         data: list[list],
#         sheet_name: str,
#         start_row: int,
#         start_col: int,
#         cell_format: str,
#         cell_format_range: list[int] | None,
#     ):
#         if cell_format_range:
#             start_row_format, start_col_format, end_row_format, end_col_format = (
#                 cell_format_range
#             )
#         else:
#             start_row_format = start_row
#             start_col_format = start_col
#             end_row_format = start_row + len(data) - 1
#             end_col_format = start_col + len(data[0]) - 1
#
#         for i, row_data in enumerate(data, start=start_row):
#             for j, value in enumerate(row_data, start=start_col):
#                 if (
#                     start_row_format <= i <= end_row_format
#                     and start_col_format <= j <= end_col_format
#                 ):
#                     self.write_cell(sheet_name, i, j, value, cell_format)
#                 else:
#                     self.write_cell(sheet_name, i, j, value)
#
#     def write_cell(
#         self,
#         sheet: str,
#         row: int,
#         column: int,
#         value,
#         cell_format: str | dict | None = None,
#     ):
#         worksheet = self.get_or_create_worksheet(sheet)
#         format_object = self._get_format_object(cell_format)
#         worksheet.write(row, column, value, format_object)
#
#     def get_or_create_worksheet(self, sheet: str):
#         if sheet not in self.writer.sheets:
#             return self.writer.book.add_worksheet(sheet)
#         return self.writer.sheets[sheet]
#
#     def _get_format_object(self, cell_format: str | dict | None):
#         if isinstance(cell_format, str):
#             return self.workbook.add_format(self.get_format(cell_format))
#         if isinstance(cell_format, dict):
#             return self.workbook.add_format(cell_format)
#         return None
#
#     def auto_fit_columns(self, sheet: str | None = None):
#         sheets = [sheet] if sheet else self.writer.sheets.keys()
#         for sheet_name in sheets:
#             self.writer.sheets[sheet_name].autofit()
#
#     def set_worksheet_color(self, color: str, sheet: str | None = None):
#         sheets = [sheet] if sheet else self.writer.sheets.keys()
#         for sheet_name in sheets:
#             self.writer.sheets[sheet_name].set_tab_color(color)
#
#     def format_column(
#         self,
#         sheet_name: str,
#         first_col: int,
#         last_col: int,
#         cell_format: str | dict,
#         width: int | None = None,
#         options: None | dict = None,
#     ):
#         worksheet = self.get_sheet(sheet_name)
#         format_object = self._get_format_object(cell_format)
#         worksheet.set_column(first_col, last_col, width, format_object, options)
#
#     def format_row(
#         self,
#         sheet_name: str,
#         row_num: int,
#         cell_format: str | dict,
#         height: None | int = None,
#         options: None | dict = None,
#     ):
#         worksheet = self.get_sheet(sheet_name)
#         format_object = self._get_format_object(cell_format)
#         worksheet.set_row(row_num, height, format_object, options)
#
#     def save(self):
#         self.writer.close()
#         self.temp_file.close()
#
#         while True:
#             try:
#                 shutil.copy(self.temp_file.name, self.file_path)
#                 Path(self.temp_file.name).unlink()
#                 logger.success("File saved successfully.")
#                 break
#             except PermissionError:
#                 logger.warning(
#                     f"Permission denied: Unable to save file at {self.file_path}."
#                 )
#                 if input("Do you want to retry? (y/n): ").strip().lower() != "y":
#                     logger.warning(f"File {self.file_path} was not saved.")
#                     break
#
#     def get_sheet(self, sheet_name: str):
#         return self.writer.sheets[sheet_name]
