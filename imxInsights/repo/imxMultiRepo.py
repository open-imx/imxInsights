from collections import OrderedDict
from pathlib import Path

import pandas as pd
from loguru import logger

from imxInsights.domain.imxObject import ImxObject
from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol
from imxInsights.repo.imxComparedRepo import ComparedMultiRepo
from imxInsights.repo.imxMultiRepoObject import ImxMultiRepoObject
from imxInsights.utils.shapely.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform


class ImxMultiRepo:
    def __init__(
        self,
        containers: list[ImxContainerProtocol | ImxSituationProtocol],
        version_safe: bool = True,
    ):
        self._validate_containers(containers, version_safe)
        self.containers: list[ImxContainerProtocol | ImxSituationProtocol] = containers
        self.container_order: list[str] = [
            container.container_id for container in self.containers
        ]
        self.tree_dict: OrderedDict[str, OrderedDict[str, list[ImxObject]]] = (
            OrderedDict()
        )
        self._keys: frozenset[str] = frozenset()
        self._process_container_objects()
        self._update_keys()

    @staticmethod
    def _validate_containers(
        containers: list[ImxContainerProtocol | ImxSituationProtocol],
        version_safe: bool,
    ) -> None:
        """Ensure containers have unique IDs and the same imx_version if version safe."""

        seen_container_ids: set[str] = set()
        first_version = containers[0].imx_version if containers else None

        def _validate_container(
            container: ImxContainerProtocol | ImxSituationProtocol,
        ) -> None:
            if container.container_id in seen_container_ids:
                raise ValueError(
                    f"Duplicate container_id '{container.container_id}' detected"
                )
            seen_container_ids.add(container.container_id)

            if version_safe and container.imx_version != first_version:
                raise ValueError(
                    f"Container '{container.container_id}' has a different imx_version. Expected '{first_version}', got '{container.imx_version}'."
                )

        for container in containers:
            _validate_container(container)

    def _process_container_objects(self):
        """Process the objects within each container and organize them in a dictionary."""
        for container in self.containers:
            container_id = container.container_id
            for imx_object in container.get_all():
                puic = imx_object.puic
                if puic not in self.tree_dict:
                    self.tree_dict[puic] = OrderedDict(
                        (cid, []) for cid in self.container_order
                    )
                self.tree_dict[puic][container_id].append(imx_object)

    def _update_keys(self) -> None:
        """Update the unique keys (puics) of the tree_dict."""
        self._keys = frozenset(self.tree_dict.keys())

    def get_keys(self) -> frozenset[str]:
        """Returns all unique keys (puics) in the tree_dict."""
        return self._keys

    def _get_objects_by_key(self, key: str | None = None) -> ImxMultiRepoObject:
        """Helper to retrieve ImxObjects by key or return default None values if the key is missing."""
        if key and key not in self._keys:
            raise ValueError(f"key:{key} not in tree.")

        imx_object = self.tree_dict.get(key or "", None)

        tester = (
            tuple(
                imx_object[container_id][0]
                if imx_object and len(imx_object[container_id]) > 0
                else None
                for container_id in self.container_order
            )
            if imx_object
            else tuple([None] * len(self.container_order))
        )
        return ImxMultiRepoObject(tester, self.container_order)

    def find(
        self,
        key: str,
    ) -> ImxMultiRepoObject:
        """Returns all ImxObject instances for a given key (puic), maintaining container order."""
        return self._get_objects_by_key(key)

    def get_all(self) -> list[ImxMultiRepoObject]:
        """Returns a list of tuples for each ImxObject, maintaining container order."""
        return [self._get_objects_by_key(key) for key in self.tree_dict]

    def get_all_types(self) -> set[str]:
        """Returns all unique types (tags) of ImxObject instances."""
        return {
            obj.tag
            for group in self.get_all() or []
            for obj in (group or [])
            if obj is not None
        }

    def get_by_types(self, object_types: list[str]) -> list[ImxMultiRepoObject]:
        """Returns all items by given types, will check first type of object."""
        return [
            item
            for item in self.get_all()
            if any(obj and obj.tag in object_types for obj in item)
        ]

    def get_all_paths(self) -> set[str]:
        """Returns all unique paths of ImxObject instances."""
        return {
            obj.path
            for group in self.get_all() or []
            for obj in (group or [])
            if obj and obj.path
        }

    def get_by_paths(self, object_paths: list[str]) -> list[ImxMultiRepoObject]:
        """Returns all items by given paths, ensuring at least one item matches the paths."""
        return [
            item
            for item in self.get_all()
            if any(obj and obj.path in object_paths for obj in item)
        ]

    def get_pandas_df(
        self,
        types: list[str] | None = None,
        paths: list[str] | None = None,
        pivot_df: bool = False,
    ) -> pd.DataFrame:
        """Returns a Pandas DataFrame of the filtered objects based on type and path."""
        imx_objects = self._filter_objects(types, paths)

        data = []
        for obj_tuple in imx_objects:
            for idx, imx_obj in enumerate(obj_tuple):
                if isinstance(imx_obj, ImxObject):
                    properties = {
                        "container_id": imx_obj.container_id,
                        "imx_situation": imx_obj.imx_situation or None,
                        "path": imx_obj.path,
                    } | imx_obj.properties
                    data.append(properties)
                else:
                    data.append({"container_id": self.container_order[idx]})
        df = pd.DataFrame(data)
        df = self._prepare_dataframe(df, pivot_df)
        return df

    def _filter_objects(
        self, types: list[str] | None, paths: list[str] | None
    ) -> list[ImxMultiRepoObject]:
        """Filter objects by types or paths."""
        imx_objects = []
        if types:
            imx_objects.extend(self.get_by_types(types))
        if paths:
            imx_objects.extend(self.get_by_paths(paths))
        if not types and not paths:
            imx_objects.extend(self.get_all())
        return imx_objects

    def _prepare_dataframe(self, df: pd.DataFrame, pivot_df: bool) -> pd.DataFrame:
        """Prepare and format the DataFrame."""
        df.set_index(["@puic", "path", "container_id"], inplace=True)
        container_order_mapping = {
            container_id: idx for idx, container_id in enumerate(self.container_order)
        }
        df = df.reset_index()
        df["T"] = df["container_id"].map(container_order_mapping)
        df.set_index(["@puic", "path", "T"], inplace=True)

        if not pivot_df:
            df.reset_index(inplace=True)

        return df

    def get_pandas_df_dict(self, pivot_df: bool = False) -> dict[str, pd.DataFrame]:
        """Returns a dictionary of DataFrames, one for each unique path."""
        return {
            path: self.get_pandas_df(paths=[path], pivot_df=pivot_df)
            for path in self.get_all_paths()
        }

    def get_geojson(
        self,
        object_path: list[str],
        container_id: str,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> ShapelyGeoJsonFeatureCollection:
        """Generate a GeoJSON feature collection from a list of object types or paths."""
        features: list[ShapelyGeoJsonFeature] = []

        for item in self.get_by_paths(object_path):
            for imx_object in item.imx_objects:
                if not imx_object:
                    break

                if imx_object.container_id != container_id:
                    break

                location = None
                if imx_object.geometry is not None:
                    location = imx_object.geometry
                if imx_object.geographic_location is not None and hasattr(
                    imx_object.geographic_location, "shapely"
                ):
                    location = imx_object.geographic_location.shapely

                if location:
                    geometry = (
                        ShapelyTransform.rd_to_wgs(location) if to_wgs else location
                    )
                    features.append(
                        ShapelyGeoJsonFeature(
                            geometry_list=[geometry],
                            properties=imx_object.properties
                            | (
                                imx_object.extension_properties
                                if extension_properties
                                else {}
                            ),
                        )
                    )
        return ShapelyGeoJsonFeatureCollection(
            features, crs=CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def create_geojson_files(
        self,
        directory_path: str | Path,
        container_id: str,
        to_wgs: bool = True,
        extension_properties: bool = False,
    ) -> None:
        """Create GeoJSON files for the specified object types or paths and save them to the given directory."""
        for path in self.get_all_paths():
            dir_path = Path(directory_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            geojson_feature_collection = self.get_geojson(
                [path],
                container_id,
                to_wgs=to_wgs,
                extension_properties=extension_properties,
            )
            geojson_file_path = dir_path / f"{path}.geojson"
            geojson_feature_collection.to_geojson_file(geojson_file_path)
            logger.success(f"GeoJSON file created and saved at {geojson_file_path}.")

    def get_container(self, container_id: str):
        container = [
            container
            for container in self.containers
            if container.container_id == container_id
        ]
        if len(container) == 1:
            return container[0]
        raise ValueError("Container not present")

    def compare(self, container_id_1: str, container_id_2: str):
        return ComparedMultiRepo(
            self.get_container(container_id_1),
            self.get_container(container_id_2),
            self.get_all(),
        )