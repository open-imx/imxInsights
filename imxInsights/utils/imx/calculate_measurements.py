# from pathlib import Path
#
# from shapely import Point
#
# from imxInsights import ImxContainer
# from imxInsights.utils.measure_3d.measureCalculator import MeasureLine
#
#
# # from imxInsights.utils.shapely.shapely_geojson import (
# #     CrsEnum,
# #     ShapelyGeoJsonFeatureCollection,
# # )
#
#
# def calculate_measurements(
#     imx: ImxContainer,
#     create_geojson_debug: bool = False,
#     out_path: Path | str | None = None,
# ):
#     if not out_path and create_geojson_debug:
#         raise ValueError("should have out_path when creating geojsons")
#     if isinstance(out_path, str):
#         out_path = Path(out_path)
#
#     out_list = []
#     measure_line_dict: dict[str, MeasureLine] = {}
#
#     for imx_object in imx.get_all():
#         geometry = imx_object.geometry
#         if not isinstance(geometry, Point):
#             continue
#
#         for ref in imx_object.refs:
#             ref_field = ref.field
#             if not ref_field.endswith("@railConnectionRef"):
#                 continue
#
#             rail_con = ref.imx_object
#             puic = rail_con.puic
#
#             measure_line = measure_line_dict.get(puic)
#             if measure_line is None:
#                 measure_line = MeasureLine(rail_con.geometry)
#                 measure_line_dict[puic] = measure_line
#
#             at_measure = imx_object.properties.get(
#                 ref_field.replace("@railConnectionRef", "@atMeasure")
#             )
#             projection_result = measure_line.project(geometry)
#
#             # if create_geojson_debug:
#             #     fc = ShapelyGeoJsonFeatureCollection(
#             #         projection_result.as_geojson_features(), crs=CrsEnum.RD_NEW_NAP
#             #     )
#             #     fc.to_geojson_file(out_path / f"{imx_object.puic}-{puic}.geojson")
#
#             out_list.append(
#                 [
#                     imx_object.puic,
#                     ref_field,
#                     puic,
#                     float(at_measure) if at_measure else None,
#                     projection_result.measure_3d,
#                     rail_con.geometry.project(geometry),
#                 ]
#             )
#
#     return out_list
