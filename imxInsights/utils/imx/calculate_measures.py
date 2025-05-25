from pathlib import Path

import pandas as pd
from openpyxl.utils import get_column_letter
from shapely import Point

from imxInsights import ImxContainer, ImxSingleFile
from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol
from imxInsights.utils.measure_3d.measureCalculator import MeasureLine
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeatureCollection,
)


def calculate_measurements(
    imx: ImxSituationProtocol | ImxContainer,
    create_geojson_debug: bool = False,
    out_path: Path | str | None = None,
):
    out_list = []
    measure_line_dict: dict[str, MeasureLine] = {}

    for imx_object in imx.get_all():
        geometry = imx_object.geometry
        if not isinstance(geometry, Point):
            continue

        for ref in imx_object.refs:
            ref_field = ref.field
            if not ref_field.endswith("@railConnectionRef"):
                continue

            rail_con = ref.imx_object
            if rail_con is None:
                continue
            puic = rail_con.puic

            measure_line = measure_line_dict.get(puic)
            if measure_line is None:
                measure_line = MeasureLine(rail_con.geometry)
                measure_line_dict[puic] = measure_line

            at_measure = imx_object.properties.get(
                ref_field.replace("@railConnectionRef", "@atMeasure")
            )
            projection_result = measure_line.project(geometry)

            if create_geojson_debug:
                if not out_path:
                    raise ValueError("No outpath")

                if isinstance(out_path, str):
                    out_path = Path(out_path)

                fc = ShapelyGeoJsonFeatureCollection(
                    projection_result.as_geojson_features(), crs=CrsEnum.RD_NEW_NAP
                )
                fc.to_geojson_file(out_path / f"{imx_object.puic}-{puic}.geojson")

            imx_measure = float(at_measure) if at_measure else None
            measure_2d = rail_con.geometry.project(geometry)

            if imx_measure and isinstance(projection_result.measure_3d, float):
                delta_imx_3d = round(imx_measure - projection_result.measure_3d, 3)
                delta_2d_3d = round(measure_2d - projection_result.measure_3d, 3)
            else:
                delta_imx_3d = None
                delta_2d_3d = None

            out_list.append(
                [
                    imx_object.puic,
                    imx_object.path,
                    imx_object.name,
                    ref_field,
                    puic,
                    imx_measure,
                    delta_imx_3d,
                    projection_result.measure_3d,
                    delta_2d_3d,
                    measure_2d,
                    projection_result.side.value,
                    projection_result.projection_status.value,
                ]
            )

    return out_list


def create_measure_check_excel(situation: ImxSituationProtocol | ImxContainer):
    out_list = [] if not situation else calculate_measurements(situation)

    df = pd.DataFrame(
        out_list,
        columns=[
            "object_puic",
            "path",
            "object name",
            "ref_field",
            "ref_field_value",
            "imx_measure",
            "imx_vs_3d_measure",
            "calculated_3d_measure",
            "2d_vs_3d_measure",
            "calculated_2d_measure",
            "side",
            "projection_status",
        ],
    )

    # write to Excel
    output_path = "measure_check-ezl.xlsx"
    with pd.ExcelWriter(output_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        worksheet = writer.sheets["Sheet1"]

        # Auto-adjust column widths
        for column_cells in worksheet.columns:
            max_length = 0
            column = column_cells[0].column  # Get the column index (1-based)
            for cell in column_cells:
                try:
                    if cell.value:
                        max_length = max(max_length, len(str(cell.value)))
                except Exception as e:
                    print(f"Auto-adjust column widths failed {e}")
            adjusted_width = max_length + 2
            worksheet.column_dimensions[
                get_column_letter(column)
            ].width = adjusted_width

        worksheet.freeze_panes = worksheet["A2"]
        worksheet.auto_filter.ref = worksheet.dimensions


if __name__ == "__main__":
    imx = ImxSingleFile("PathToImx")
    if imx.new_situation:
        create_measure_check_excel(imx.new_situation)
