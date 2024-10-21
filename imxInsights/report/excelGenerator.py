import shutil
import tempfile
from pathlib import Path

import pandas as pd


class ExcelReport:
    def __init__(self, file_path: str | Path):
        self.file_path = file_path
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False)
        self.writer = pd.ExcelWriter(self.temp_file.name, engine="xlsxwriter")

    def add_dataframe(
        self,
        df: pd.DataFrame,
        sheet_name: str,
        start_row: int = 0,
        start_col: int = 0,
        index: bool = True,
        header: bool = True,
    ):
        df.to_excel(
            self.writer,
            sheet_name=sheet_name,
            index=index,
            header=header,
            startrow=start_row,
            startcol=start_col,
        )
        return len(df) + start_row

    def add_list_of_lists(
        self,
        data: list[list],
        sheet_name: str,
        start_row: int = 0,
        start_col: int = 0,
        header: bool = True,
        index: bool = True,
    ):
        df = pd.DataFrame(data)
        self.add_dataframe(
            df,
            sheet_name,
            start_row=start_row,
            start_col=start_col,
            header=header,
            index=index,
        )
        return len(data) + start_row

    def auto_fit_columns(self, sheet: str | None = None):
        if sheet:
            self.writer.sheets[sheet].autofit()
        else:
            for sheet in self.writer.sheets:
                self.writer.sheets[sheet].autofit()

    def set_worksheet_color(self, color: str, sheet: str | None = None):
        if sheet:
            self.writer.sheets[sheet].set_tab_color(color)
        else:
            for sheet in self.writer.sheets:
                self.writer.sheets[sheet].set_tab_color(color)

    def save(self):
        self.writer.close()
        self.temp_file.close()
        shutil.copy(self.temp_file.name, self.file_path)
        Path(self.temp_file.name).unlink()

    def get_sheet(self, sheet_name: str):
        return self.writer.sheets[sheet_name]
