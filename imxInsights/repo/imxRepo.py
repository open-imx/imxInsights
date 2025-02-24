import tempfile
import uuid
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from datetime import datetime
from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions import ImxException
from imxInsights.repo.imxObjectTree import ObjectTree
from imxInsights.utils.report_helpers import (
    app_info_df,
    shorten_sheet_name,
    upper_keys_with_index,
    write_df_to_sheet,
)
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform


class ImxRepo:
    """
    Represents an IMX container.

    Args:
        imx_file_path: The path to the IMX container or IMX File.

    Attributes:
        container_id: UUID4 of the container
        path: Path of the IMX container or IMX File.
    """

    def __init__(self, imx_file_path: Path | str):
        # todo: imx_file_path should be only Path
        self._tree: ObjectTree = ObjectTree()
        self.container_id: str = str(uuid.uuid4())
        self.imx_version: str | None = None
        self.file_path: Path = Path(imx_file_path)
        self.path: Path = self._get_file_path(imx_file_path=imx_file_path)

    def _get_file_path(self, imx_file_path: Path | str) -> Path:
        """
        Get Path of temp zip folder of to directory containing imx files.

        Args:
            imx_file_path: The path to the Imx files directory or zip.

        """
        if zipfile.is_zipfile(imx_file_path):
            return self._parse_zip_container(imx_file_path)
        else:
            return Path(imx_file_path)

    @staticmethod
    def _parse_zip_container(imx_container_as_zip: str | Path) -> Path:
        """
        Parse the IMX container if it's a zip file.

        Args:
            imx_container_as_zip (Union[str, Path]): The path to the IMX container as a zip file.

        Returns:
            Path: The extracted directory path of the zip container.
        """
        temp_dir = tempfile.mkdtemp()
        temp_path = Path(temp_dir)
        with zipfile.ZipFile(imx_container_as_zip, "r") as zip_ref:
            zip_ref.extractall(temp_path)
        return Path(temp_path)

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
        Retrieve build exceptions from the tree structure.

        This method returns any build exceptions that occurred during the build process. The result is a dictionary
        where the keys are strings representing different build steps  or processes, and the values are lists
        of `ImxException` instances.

        Returns:
            A dictionary where the keys represent the build processes step, and the values are lists of `ImxException` that were raised.
        """
        return self._tree.build_exceptions.exceptions

    @staticmethod
    def _add_nice_display(imx_object, props):
        # TODO: not sure, if we overwrite the ref, or add a column...
        add_column = True

        ref_lookup_map = {
            ref.lookup: ref.display for ref in imx_object.refs
        }  # Create a lookup map once

        result = {}
        for key, value in props.items():
            formatted_value = "\n".join(value.split(" "))
            result[key] = formatted_value

            if key.endswith("Ref"):
                if value in ref_lookup_map:
                    result[f"{key}|display" if add_column else key] = ref_lookup_map[
                        value
                    ]

            elif key.endswith("Refs"):
                ref_displays = [
                    ref_lookup_map[item]
                    for item in value.split(" ")
                    if item in ref_lookup_map
                ]
                if ref_displays:
                    result[f"{key}|display" if add_column else key] = "\n".join(
                        ref_displays
                    )
        return result

    @staticmethod
    def _extract_overview_properties(
        imx_object, input_props=None, nice_display_ref=False
    ):
        props = (
            imx_object.get_imx_property_dict()
            if input_props is None
            else {
                key: value
                for key, value in imx_object.get_imx_property_dict().items()
                if key in input_props
            }
        )

        if nice_display_ref:
            props = ImxRepo._add_nice_display(imx_object, props)

        return props

    def get_pandas_df(
        self,
        object_type_or_path: list[str] | None = None,
        puic_as_index: bool = True,
        nice_display_ref: bool = True,
    ) -> pd.DataFrame:
        """
        Get Pandas dataframe of one value object type or limited view of all objects.

        When using an object type or path, all properties will be flattened. When getting a dataframe of all objects,
        most attributes will be stripped except for some metadata. In both cases, it will include parent puic,
        path.

        Args:
            object_type_or_path: path or imx type to get df of
            puic_as_index: if true puic value will be the index
            nice_display_ref: if we process refs as nice display

        Returns:
            pd.DataFrame: pandas dataframe of the object properties
        """
        if object_type_or_path is None:
            props_in_overview = [
                "@puic",
                "tag",
                "path",
                "@name",
                "Location.GeographicLocation.@accuracy",
                "Location.GeographicLocation.@dataAcquisitionMethod",
                "Metadata.@isInService",
                "Metadata.@lifeCycleStatus",
                "Metadata.@source",
            ]
            records = [
                self._extract_overview_properties(
                    item, props_in_overview, nice_display_ref=False
                )
                for item in self.get_all()
            ]
        else:
            value_objects = []
            for item in object_type_or_path:
                if "." in item:
                    value_objects.extend(self.get_by_paths([item]))
                else:
                    value_objects.extend(self.get_by_types([item]))

            records = [
                self._extract_overview_properties(
                    item, nice_display_ref=nice_display_ref
                )
                for item in value_objects
            ]

        df = pd.DataFrame.from_records(records)
        if not df.empty and puic_as_index:
            df.set_index("@puic", inplace=False)
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
                out_dict[imx_type] = self.get_pandas_df([imx_type])

        for imx_path in self.get_all_paths():
            out_dict[imx_path] = self.get_pandas_df([imx_path])

        return out_dict

    def get_pandas_df_overview(self, nice_display_ref: bool = True) -> pd.DataFrame:
        nodes = list(self.get_all())
        paths = [self._get_full_path(node) for node in nodes]

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
        properties = [
            self._extract_overview_properties(
                node, list_of_columns, nice_display_ref=nice_display_ref
            )
            for node in nodes
        ]

        max_depth = max(len(path) for path in paths)
        padded_paths = [
            path[:-1] + [""] * (max_depth - len(path)) + [path[-1]] for path in paths
        ]

        df = pd.DataFrame(properties)
        index = pd.MultiIndex.from_tuples(
            padded_paths, names=[f"Level{i + 1}" for i in range(max_depth)]
        )
        df.index = index
        return df

    def get_geojson(
        self,
        object_path: list[str],
        to_wgs: bool = True,
        extension_properties: bool = False,
        nice_display_ref: bool = False,
    ) -> ShapelyGeoJsonFeatureCollection:
        """
        Generate a GeoJSON feature collection from a list of object types or paths.

        Args:
            object_path: A list of object paths used to fetch the corresponding data.
            to_wgs: convert to WGS84
            extension_properties: add extension properties to geojson
            nice_display_ref: add nice display refs

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
                geometry = (
                    [ShapelyTransform.rd_to_wgs(location)] if to_wgs else [location]
                )
            else:
                geometry = []

            properties = self._extract_overview_properties(
                item, nice_display_ref=nice_display_ref
            )

            features.append(
                ShapelyGeoJsonFeature(
                    geometry,
                    properties,
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
        nice_display_ref: bool = True,
    ):
        """
        Create GeoJSON files for the specified object types or paths and save them to the given directory.

        Args:
            directory_path: The directory where the GeoJSON files will be created.
            to_wgs: convert to WGS84
            extension_properties: add extension properties to geojson
            nice_display_ref: add nice display refs

        """
        for path in self.get_all_paths():
            dir_path = Path(directory_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            geojson_feature_collection = self.get_geojson(
                [path],
                to_wgs=to_wgs,
                extension_properties=extension_properties,
                nice_display_ref=nice_display_ref,
            )
            geojson_file_path = dir_path / f"{path}.geojson"
            geojson_feature_collection.to_geojson_file(geojson_file_path)
            logger.success(f"GeoJSON file created and saved at {geojson_file_path}.")

    @staticmethod
    def _get_full_path(node):
        """Recursively get the path from a node to the top ancestor."""
        path: list[str] = []
        current = node
        while current:
            path.insert(0, current.puic)
            current = current.parent
        path.insert(0, node.path.split(".")[0])
        path.append(node.path)
        return path

    def to_excel(self, file_path: str | Path):
        """Writes the comparison results to an Excel file, applying formatting."""
        pandas_dict = dict(sorted(self.get_pandas_df_dict().items()))
        pandas_dict = upper_keys_with_index(pandas_dict)

        overview_df = self.get_pandas_df_overview()

        file_path = Path(file_path).resolve()
        with pd.ExcelWriter(file_path, engine="xlsxwriter") as writer:
            index_data = []

            process_data = {
                "FilePath": f"{self.file_path}",
                "Run Date": f"{datetime.now()}",
            }
            write_df_to_sheet(
                writer,
                "INFO",
                app_info_df(process_data),
                index=False,
                header=False,
                auto_filter=False,
            )
            index_data.append(["INFO", "AppInfo", '=HYPERLINK("#INFO!A1", "Go")'])

            index_data.append(
                [
                    "META_OVERVIEW",
                    "Meta Overview",
                    '=HYPERLINK("#META_OVERVIEW!A1", "Go")',
                ]
            )
            for key, df in pandas_dict.items():
                sheet_name = shorten_sheet_name(key)
                index_data.append(
                    [sheet_name, key, f'=HYPERLINK("#{sheet_name}!A1", "Go the sheet")']
                )
            index_df = pd.DataFrame(
                index_data, columns=["Sheet Name", "Full Name", "Link"]
            )
            write_df_to_sheet(
                writer, "INDEX", index_df, index=True, header=True, auto_filter=True
            )

            overview_df.to_excel(writer, sheet_name="META_OVERVIEW", index=False)
            write_df_to_sheet(
                writer,
                "META_OVERVIEW",
                overview_df,
                index=True,
                header=True,
                auto_filter=True,
            )

            for key, df in pandas_dict.items():
                sheet_name = shorten_sheet_name(key)
                write_df_to_sheet(
                    writer,
                    sheet_name,
                    df,
                    index=False,
                    header=True,
                    auto_filter=True,
                )
