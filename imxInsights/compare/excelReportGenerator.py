import sys
from datetime import datetime

import pandas as pd
from loguru import logger
from pandas import DataFrame
from tqdm import tqdm

from imxInsights.file.singleFileImx.imxSituation import ImxSituation
from imxInsights.utils.excel_helpers import shorten_sheet_name
from imxInsights.utils.flatten_unflatten import hash_sha256


class ExcelReportGenerator:
    def __init__(self, pandas_df_dict, containers, container_order):
        self.pandas_df_dict: dict[str, DataFrame] = pandas_df_dict
        self.containers: list[ImxSituation] = containers
        self.container_order: tuple[str, ...] = container_order

    def create_excel(
        self,
        file_path: str = f'diff_excel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
    ):
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            self._create_info_sheet(writer)
            self._create_meta_overview(writer)
            self._create_diff_sheets(writer)

    def _create_info_sheet(self, writer):
        workbook = writer.book
        info_worksheet = workbook.add_worksheet("Info")

        info_data = [
            ["ImxInsights", ""],
            ["Processing Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S")],
        ]

        t1_container = next(
            c for c in self.containers if c.container_id == self.container_order[0]
        )
        t2_container = next(
            c for c in self.containers if c.container_id == self.container_order[1]
        )

        info_data.append(["", ""])
        info_data.append(["T1", ""])
        info_data.append(
            [
                "imx version",
                t1_container.imx_version if t1_container.imx_version else "",
            ]
        )

        self._add_container_files_info(info_data, t1_container)
        info_data.append(["", ""])
        info_data.append(["T2", ""])
        info_data.append(
            [
                "imx version",
                t2_container.imx_version if t2_container.imx_version else "",
            ]
        )

        self._add_container_files_info(info_data, t2_container)

        for row_num, (key, value) in enumerate(info_data):
            info_worksheet.write(row_num, 0, key)
            info_worksheet.write(row_num, 1, value)

    def _add_container_files_info(self, info_data, container):
        if not hasattr(container, "files"):
            info_data.append(["path", container.path.name])
            info_data.append(["calculated hash", hash_sha256(container.path)])
            info_data.append(["situation", container.situation_type.value])
        else:
            info_data.append(["path", container.path.name])
            for file in container.files:
                if file is not None:
                    info_data.append(["  * file name", file.path.name])
                    info_data.append(["    - file hash", file.file_hash])
                    info_data.append(["    - calculated hash", hash_sha256(file.path)])
                    if hasattr(file, "base_reference"):
                        info_data.append(
                            [
                                "    - base reference file",
                                file.base_reference.parent_document_name,
                            ]
                        )
                        info_data.append(
                            [
                                "    - base reference hash",
                                file.base_reference.parent_hashcode,
                            ]
                        )

    def _create_diff_sheets(self, writer):
        sorted_dict = dict(sorted(self.pandas_df_dict.items()))

        with tqdm(total=len(sorted_dict), file=sys.stdout) as pbar:  # type: ignore
            for object_type, dataframe in sorted_dict.items():
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                pbar.set_description(
                    f"{current_time} | {logger.level('INFO').name}    | processing {object_type}"
                )

                sheet_name_short = shorten_sheet_name(object_type)
                dataframe.to_excel(writer, sheet_name=sheet_name_short, index=False)

                worksheet = writer.sheets[sheet_name_short]

                if isinstance(dataframe, DataFrame):
                    if dataframe["status"].eq("unchanged").all():
                        worksheet.set_tab_color("#808080")
                else:
                    if dataframe.data["status"].eq("unchanged").all():
                        worksheet.set_tab_color("#808080")

                wrap_format = writer.book.add_format({"text_wrap": True})
                if isinstance(dataframe, DataFrame):
                    for idx, col in enumerate(dataframe.columns):
                        max_length = (
                            max(dataframe[col].astype(str).map(len).max(), len(col)) + 2
                        )  # type: ignore
                        worksheet.set_column(idx, idx, max_length, wrap_format)
                else:
                    for idx, col in enumerate(dataframe.data.columns):
                        max_length = (
                            max(
                                dataframe.data[col].astype(str).map(len).max(), len(col)
                            )
                            + 2
                        )  # type: ignore
                        worksheet.set_column(idx, idx, max_length, wrap_format)

                pbar.update(1)

            pbar.set_description(
                f"{current_time} | {logger.level('INFO').name}     | processing"
            )

        logger.success("Compair Excel generated")

    def _create_meta_overview(self, writer):
        out_df = pd.DataFrame()

        for object_type, df in self.pandas_df_dict.items():
            list_of_columns = [
                "tag",
                "parentRef",
                "@puic",
                "@name",
                "status",
                "Metadata.@isInService",
                "Metadata.@lifeCycleStatus",
                "Metadata.@originType",
                "Metadata.@registrationTime",
                "Metadata.@source",
            ]
            existing_columns = [col for col in list_of_columns if col in df.columns]
            if isinstance(df, DataFrame):
                new_df = df[existing_columns]
            else:
                new_df = df.data[existing_columns]
            out_df = pd.concat([out_df, new_df], axis=0)

        out_df.to_excel(writer, sheet_name="MetaOverview", index=False)
