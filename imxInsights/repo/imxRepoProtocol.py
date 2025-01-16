from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path
from typing import Protocol, runtime_checkable

import pandas as pd

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions import ImxException
from imxInsights.repo.imxObjectTree import ObjectTree
from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeatureCollection


@runtime_checkable
class ImxRepoProtocol(Protocol):
    container_id: str
    imx_version: str | None
    path: Path
    _tree: ObjectTree

    def get_all(self) -> Iterable[ImxObject]:
        """Retrieves all objects in the tree."""
        ...

    def find(self, key: str | ImxObject) -> ImxObject | None:
        """Finds an object in the tree by its key or ImxObject."""
        ...

    def get_types(self) -> list[str]:
        """Retrieves all unique object types in the tree."""
        ...

    def get_by_types(self, object_types: list[str]) -> list[ImxObject]:
        """Retrieves objects of specified types from the tree."""
        ...

    def get_all_paths(self) -> list[str]:
        """Retrieves all unique object paths in the tree."""
        ...

    def get_by_paths(self, object_paths: list[str]) -> list[ImxObject]:
        """Retrieves objects of specified paths from the tree."""
        ...

    def get_keys(self) -> list[str]:
        """Returns the set of keys currently in the tree dictionary."""
        ...

    def get_build_exceptions(self) -> defaultdict[str, list[ImxException]]:
        """Retrieve build exceptions from the tree structure."""
        ...

    def get_pandas_df(
        self, object_type_or_path: list[str] | None = None, puic_as_index: bool = True
    ) -> pd.DataFrame:
        """Get Pandas dataframe of one value object type or limited view of all objects."""
        ...

    def get_pandas_df_dict(
        self, key_based_on_type: bool = False
    ) -> dict[str, pd.DataFrame]:
        """Get a dictionary of Pandas dataframe of all types based on keys or path."""
        ...

    def get_pandas_df_overview(self) -> pd.DataFrame:
        """Generates a DataFrame with specific population properties."""
        ...

    def get_geojson(
        self,
        object_path: list[str],
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> ShapelyGeoJsonFeatureCollection:
        """Generate a GeoJSON feature collection from a list of object types or paths."""
        ...

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> None:
        """Create GeoJSON files for the specified object types or paths and save them to the given directory."""
        ...
