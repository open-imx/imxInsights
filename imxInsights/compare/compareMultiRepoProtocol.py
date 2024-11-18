# from pathlib import Path
# from typing import Protocol
#
# from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeatureCollection
#
#
# class ImxCompareMultiRepoProtocol(Protocol):
#     def create_excel(
#         self,
#         file_path: str | None = None,
#         add_analyse: bool = False,
#         styled_df: bool = True,
#     ):
#         """Create an Excel file to save the diff data."""
#         ...
#
#     def get_geojson(
#         self,
#         object_paths: list[str],
#         to_wgs: bool = True,
#     ) -> ShapelyGeoJsonFeatureCollection:
#         """Generate a GeoJSON feature collection for specified object paths."""
#         ...
#
#     def create_geojson_files(
#         self,
#         directory_path: str | Path,
#         to_wgs: bool = True,
#     ) -> None:
#         """Create and save GeoJSON files for each object in the diff data."""
#         ...
