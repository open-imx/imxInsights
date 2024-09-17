from datetime import datetime

import pandas as pd

from imxInsights.utils.excel_helpers import shorten_sheet_name
from imxInsights.utils.flatten_unflatten import hash_sha256
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    df_sort_by_list,
    styler_highlight_changes,
)


class ExcelReportGenerator:
    def __init__(self, diff, containers, container_order):
        self.diff = diff
        self.containers = containers
        self.container_order = container_order

        # # below should be moved to create excel!
        #
        # _ = {}
        # for key, value in diff_dict.items():
        #     _[key] = value.diff_string
        #     if value.analyse is not None:
        #         _[f"{key}_analyse"] = value.analyse["display"] # TODO: make proper analyse object.
        #
        # _["status"] = self.determine_overall_status(_)
        # # set status, if all removed than its deleted, if all is created then its added, if change then it's changed if all unchanged then unchanged
        # sorted_dict = {k: _[k] for k in sorted(_)}
        # out_dict[tag].append(sorted_dict)

    def create_excel(
        self,
        file_path: str = f'diff_excel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx',
    ):
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            self._create_info_sheet(writer)
            self._create_diff_sheets(writer)

    def _create_info_sheet(self, writer):
        workbook = writer.book
        info_worksheet = workbook.add_worksheet("Info")

        info_data = [
            ["ImxInsights", "v0.2.0-alpha"],
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
        info_data.append(["imx version", t1_container.imx_version])

        self._add_container_files_info(info_data, t1_container)
        info_data.append(["", ""])
        info_data.append(["T2", ""])
        info_data.append(["imx version", t2_container.imx_version])

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
        sorted_sheet_names = sorted(self.diff.keys())

        for sheet_name in sorted_sheet_names:
            df = pd.DataFrame(
                [item.get_change_dict() for item in self.diff[sheet_name]]
            )

            extension_columns = [
                col for col in df.columns if col.startswith("extension")
            ]
            columns_to_front = ["tag", "@puic", "status"]
            df = df_columns_sort_start_end(df, columns_to_front, extension_columns)

            status_order = ["created", "changed", "unchanged", "deleted"]
            df = df_sort_by_list(df, status_order)

            columns_to_strip = ["tag", "@puic"]
            for col in columns_to_strip:
                df[col] = df[col].str.replace(r"^[+-]{2}", "", regex=True)

            styled_df = df.style.map(styler_highlight_changes)  # type: ignore

            sheet_name_short = shorten_sheet_name(sheet_name)
            styled_df.to_excel(writer, sheet_name=sheet_name_short, index=False)

            worksheet = writer.sheets[sheet_name_short]

            if df["status"].eq("unchanged").all():
                worksheet.set_tab_color("#808080")

            wrap_format = writer.book.add_format({"text_wrap": True})
            for idx, col in enumerate(df.columns):
                max_length = max(df[col].astype(str).map(len).max(), len(col)) + 2  # type: ignore
                worksheet.set_column(idx, idx, max_length, wrap_format)
