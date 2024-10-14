import tempfile
import uuid
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions import ImxException
from imxInsights.repo.tree.imxObjectTree import ObjectTree
from imxInsights.utils.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)
from imxInsights.utils.shapely_transform import ShapelyTransform


class ImxRepo:
    """
    Represents an IMX container.

    Args:
        imx_file_path: The path to the IMX container or IMX File.

    Attributes:
        container_id: UUID4 of the container
        path: Path of the IMX container or IMX File.
    """

    # todo: maybe we should inheritance from the tree so we dont need to duplicated the methods

    def __init__(self, imx_file_path: Path | str):
        # todo: imx_file_path should be only Path
        self.container_id: str = str(uuid.uuid4())
        self._tree: ObjectTree = ObjectTree()
        self.imx_version: str | None = None
        if zipfile.is_zipfile(imx_file_path):
            imx_file_path = self._parse_zip_container(imx_file_path)
        elif isinstance(imx_file_path, str):
            imx_file_path = Path(imx_file_path)
        self.path: Path = (
            imx_file_path if isinstance(imx_file_path, Path) else Path(imx_file_path)
        )

    @staticmethod
    def _parse_zip_container(imx_container_as_zip: str | Path):
        """
        Parse the IMX container if it's a zip file.

        Args:
            imx_container_as_zip (Union[str, Path]): The path to the IMX container as a zip file.

        Returns:
            Path: The extracted directory path of the zip container.
        """
        with tempfile.TemporaryDirectory(delete=False) as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(imx_container_as_zip, "r") as zip_ref:
                zip_ref.extractall(temp_path)
            return temp_path

    def get_all(self) -> Iterable[ImxObject]:
        """
        Retrieves all objects in the tree.

        Returns:
            Iterable[ImxObject]: An iterable of all ImxObjects.

        """

        return self._tree.get_all()

    def find(self, key: str | ImxObject) -> ImxObject | None:
        """
        Finds an object in the tree by its key or ImxObject.

        Args:
            key (str | ImxObject): The key or ImxObject to find.

        Returns:
            ImxObject | None: The found ImxObject, or None if not found.
        """
        return self._tree.find(key)

    def get_types(self) -> list[str]:
        """
        Retrieves all unique object types in the tree.

        Returns:
            list[str]: A list of all unique object types.
        """
        return self._tree.get_all_types()

    def get_by_types(self, object_types: list[str]) -> list[ImxObject]:
        """
        Retrieves objects of specified types from the tree.

        Args:
            object_types (list[str]): The list of object types to retrieve.

        Returns:
            list[ImxObject]: The list of matching ImxObjects.
        """
        return self._tree.get_by_types(object_types)

    def get_all_paths(self) -> list[str]:
        """
        Retrieves all unique object paths in the tree.

        Returns:
            list[str]: A list of all unique object paths.
        """
        return self._tree.get_all_paths()

    def get_by_paths(self, object_paths: list[str]) -> list[ImxObject]:
        """
        Retrieves objects of specified paths from the tree.

        Args:
            object_paths (list[str]): The list of object paths to retrieve.

        Returns:
            list[ImxObject]: The list of matching ImxObjects.
        """
        return self._tree.get_by_paths(object_paths)

    def get_keys(self) -> list[str]:
        """
        Returns the set of keys currently in the tree dictionary.

        Returns:
            frozenset[str]: The set of keys in the tree dictionary.
        """
        return list(self._tree.keys)

    def get_build_exceptions(self) -> defaultdict[str, list[ImxException]]:
        """
        todo: make docs
        """
        return self._tree.build_extensions.exceptions

    def get_pandas_df(
        self, object_type_or_path: str | None = None, puic_as_index: bool = True
    ) -> pd.DataFrame:
        """
        Get Pandas dataframe of one value object type or limited view of all objects.

        When using an object type or path, all properties will be flattened. When getting a dataframe of all objects,
        most attributes will be stripped except for some metadata. In both cases, it will include parent puic,
        path.

        Args:
            object_type_or_path: path or imx type to get df of
            puic_as_index: if true puic value will be the index

        Returns:
            pd.DataFrame: pandas dataframe of the object properties
        """

        def extract_overview_properties(item, props_in_overview=None):
            props = (
                item.properties
                if props_in_overview is None
                else {
                    key: value
                    for key, value in item.properties.items()
                    if key in props_in_overview
                }
            )
            return {
                "puic": item.puic,
                "path": item.path,
                "parent": item.parent.puic if item.parent is not None else "",
                "name": item.name,
            } | props

        if object_type_or_path is None:
            props_in_overview = [
                "Location.GeographicLocation.@accuracy",
                "Location.GeographicLocation.@dataAcquisitionMethod",
                "Metadata.@isInService",
                "Metadata.@lifeCycleStatus",
                "Metadata.@source",
            ]
            records = [
                extract_overview_properties(item, props_in_overview)
                for item in self.get_all()
            ]

        else:
            if "." in object_type_or_path:
                value_objects = self.get_by_paths([object_type_or_path])
            else:
                value_objects = self.get_by_types([object_type_or_path])

            records = [extract_overview_properties(item) for item in value_objects]

        df = pd.DataFrame.from_records(records)
        if not df.empty and puic_as_index:
            df.set_index("puic", inplace=True)
            df.fillna("", inplace=True)

        return df

    def get_pandas_df_dict(
        self, key_based_on_type: bool = False
    ) -> dict[str, pd.DataFrame]:
        """
        Get a dictionary of Pandas dataframe of all type bases on keys or path.

        Args:
            key_based_on_type: if true key based on type, else on path

        Returns: dictionary of pandas dataframe

        """
        out_dict = {}
        if key_based_on_type:
            for imx_type in self.get_types():
                out_dict[imx_type] = self.get_pandas_df(imx_type)

        for imx_path in self.get_all_paths():
            out_dict[imx_path] = self.get_pandas_df(imx_path)

        return out_dict

    def get_geojson(
        self,
        object_path: list[str],
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> ShapelyGeoJsonFeatureCollection:
        """
        Generate a GeoJSON feature collection from a list of object types or paths.

        Args:
            object_path: A list of object paths used to fetch the corresponding data.
            to_wgs: convert to WGS84
            extension_properties: add extension properties to geojson

        Returns:
            ShapelyGeoJsonFeatureCollection: A GeoJSON feature collection containing the geographical features.

        """
        features: list[ShapelyGeoJsonFeature] = []
        for item in self.get_by_paths(object_path):
            location = None
            if item.geometry is not None:
                location = item.geometry
            if item.geographic_location is not None and hasattr(
                item.geographic_location, "shapely"
            ):
                location = item.geographic_location.shapely

            if location:
                geometry = ShapelyTransform.rd_to_wgs(location) if to_wgs else location
                features.append(
                    ShapelyGeoJsonFeature(
                        [geometry],
                        item.properties
                        | (item.extension_properties if extension_properties else {}),
                    )
                )
        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ):
        """
        Create GeoJSON files for the specified object types or paths and save them to the given directory.

        Args:
            directory_path: The directory where the GeoJSON files will be created.
            to_wgs: convert to WGS84
            extension_properties: add extension properties to geojson

        """
        for path in self.get_all_paths():
            dir_path = Path(directory_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            geojson_feature_collection = self.get_geojson(
                [path], to_wgs=to_wgs, extension_properties=extension_properties
            )
            geojson_file_path = dir_path / f"{path}.geojson"
            geojson_feature_collection.to_geojson_file(geojson_file_path)
            logger.success(f"GeoJSON file created and saved at {geojson_file_path}.")
