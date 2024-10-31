from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING

import pandas as pd
from loguru import logger
from tqdm import tqdm

from imxInsights.report.excelGenerator import ExcelReport
from imxInsights.utils.excel_helpers import shorten_sheet_name

if TYPE_CHECKING:
    from imxInsights import ImxContainer
    from imxInsights.file.singleFileImx.imxSituation import ImxSituation


class DiffExcel(ExcelReport):
    def __init__(
        self,
        file_path: str | Path,
        diff_df_dict: dict[str, pd.DataFrame],
        container_order: tuple[str, ...],
        containers: list[ImxSituation | ImxContainer],
    ):
        super().__init__(file_path)
        self.diff_df_dict = diff_df_dict
        self.container_order = container_order
        self.containers = containers

        self.create_info_sheet()
        self.index_sheet = self.get_or_create_worksheet("index")
        self.create_metadata_overview()
        self.create_object_sheets()

        self.auto_fit_columns()

    def create_info_sheet(self):
        next_row = self.add_list_of_lists(
            [
                ["Comparison report"],
                [f"ImxInsights ({"aaaa"})"],
                ["https://open-imx.nl/"],
            ],
            sheet_name="info",
            start_row=1,
            start_col=1,
            header=False,
            index=False,
            cell_format="h1",
            cell_format_range=[1, 1, 1, 1],
        )
        self.format_row("info", 2, "h3")

        cell_hover = {  # for row hover use <tr> instead of <td>
            "selector": "td:hover",
            "props": [("background-color", "#ffffb3")],
        }

        index = {  # for row hover use <tr> instead of <td>
            "selector": "th",
            "props": [
                ("background-color", "#000066"),
                ("color", "green"),
                ("text-align", "left"),
            ],
        }

        sorted_objects = sorted(
            self.containers,
            key=lambda obj: self.container_order.index(obj.container_id)
            if obj.container_id in self.container_order
            else float("inf"),
        )

        for idx, item in enumerate(sorted_objects, start=1):
            self.write_cell("info", next_row + 1, 1, f"IMX T{idx}", "h2")
            imx_info_df = item.dataframes.combined_info_df(pivot_df=True)

            styled_imx_info_df = imx_info_df.style.set_properties(
                subset=None, **{"background-color": "#ECE3FF", "color": "black"}
            ).map(lambda x: "border: 1px solid;")  # type: ignore
            styled_imx_info_df = styled_imx_info_df.set_table_styles(
                [cell_hover, index]
            )

            next_row = self.add_dataframe(
                styled_imx_info_df,
                "info",
                start_row=next_row + 2,
                start_col=1,
                header=False,
            )

    def create_metadata_overview(self):
        # TODO: create metadata overview for diff report
        pass

    def create_object_sheets(self):
        with tqdm(total=len(self.diff_df_dict.keys()), file=sys.stdout) as pbar:  # type: ignore
            current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
            pbar.set_description(
                f"{current_time} | {logger.level('INFO').name}     | Writing Excel File"
            )
            for key, value in self.diff_df_dict.items():
                sheet_name = shorten_sheet_name(key)
                next_row = self.add_dataframe(
                    value, sheet_name, start_row=0, start_col=0, header=True
                )
                worksheet = self.get_or_create_worksheet(sheet_name)
                worksheet.freeze_panes(1, 0)
                worksheet.autofilter(0, 0, 0, next_row)

                # todo: check if all not changed, then we should make the sheet gray

                pbar.update(1)
