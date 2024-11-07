from collections.abc import Iterable
from pathlib import Path
from typing import Protocol

from imxInsights.domain.imxObject import ImxObject
from imxInsights.utils.shapely_geojson import ShapelyGeoJsonFeatureCollection


class ImxCompareMultiRepoProtocol(Protocol):
    def get_all(self) -> Iterable[ImxObject]:
        """Retrieves all objects in the tree."""
        ...

    def find(self, key: str | ImxObject) -> list[ImxObject] | None:
        """Finds an object in the tree by its key or ImxObject."""
        ...

    def create_excel(
        self,
        file_path: str | None = None,
        add_analyse: bool = False,
        styled_df: bool = True,
    ):
        """Create an Excel file to save the diff data."""
        ...

    def get_geojson(
        self,
        object_paths: list[str],
        to_wgs: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        """Generate a GeoJSON feature collection for specified object paths."""
        ...

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
    ):
        """Create and save GeoJSON files for each object in the diff data."""
        ...
