from collections import OrderedDict
from pathlib import Path
from typing import Protocol, runtime_checkable

import pandas as pd

from imxInsights.domain.imxObject import ImxObject
from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol
from imxInsights.repo.imxMultiRepoObject import ImxMultiRepoObject
from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeatureCollection


@runtime_checkable
class ImxMultiRepoProtocol(Protocol):
    containers: list[ImxContainerProtocol | ImxSituationProtocol]
    container_order: list[str]
    tree_dict: OrderedDict[str, OrderedDict[str, list[ImxObject]]]
    _keys: frozenset[str]

    def get_keys(self) -> list[str]:
        """Returns all unique keys (puics) in the tree_dict."""
        ...

    def _get_objects_by_key(self, key: str | None = None) -> ImxMultiRepoObject:
        """Helper to retrieve ImxObjects by key or return default None values if the key is missing."""
        ...

    def find(self, key: str) -> ImxMultiRepoObject:
        """Returns all ImxObject instances for a given key (puic), maintaining container order."""
        ...

    def get_all(self) -> list[ImxMultiRepoObject]:
        """Returns a list of tuples for each ImxObject, maintaining container order."""
        ...

    def get_all_types(self) -> set[str]:
        """Returns all unique types (tags) of ImxObject instances."""
        ...

    def get_by_types(self, object_types: list[str]) -> list[ImxMultiRepoObject]:
        """Returns all items by given types, will check first type of object."""
        ...

    def get_all_paths(self) -> set[str]:
        """Returns all unique paths of ImxObject instances."""
        ...

    def get_by_paths(self, object_paths: list[str]) -> list[ImxMultiRepoObject]:
        """Returns all items by given paths, ensuring at least one item matches the paths."""
        ...

    def get_pandas_df(
        self,
        types: list[str] | None = None,
        paths: list[str] | None = None,
        pivot_df: bool = False,
    ) -> pd.DataFrame:
        """Returns a Pandas DataFrame of the filtered objects based on type and path."""
        ...

    def get_pandas_df_dict(self, pivot_df: bool = False) -> dict[str, pd.DataFrame]:
        """Returns a dictionary of DataFrames, one for each unique path."""
        ...

    def get_pandas_df_overview(self) -> pd.DataFrame:
        """Generates a DataFrame with specific population properties."""
        ...

    def get_geojson(
        self,
        object_path: list[str],
        container_id: str,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> ShapelyGeoJsonFeatureCollection:
        """Generate a GeoJSON feature collection from a list of object types or paths."""
        ...

    def create_geojson_files(
        self,
        directory_path: str | Path,
        container_id: str,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> None:
        """Create GeoJSON files for the specified object types or paths and save them to the given directory."""
        ...
