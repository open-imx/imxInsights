import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
from loguru import logger
from tqdm import tqdm

from imxInsights.compare.changedImxObject import ChangedImxObject
from imxInsights.compare.changes import ChangeStatus, get_object_changes
from imxInsights.compare.geometryChange import GeometryChange
from imxInsights.compare.helpers import (
    merge_dict_keep_first_key,
    parse_dict_to_value_objects,
    remove_empty_dicts,
    transform_dict,
)
from imxInsights.report.diffExcel import DiffExcel
from imxInsights.utils.pandas_helpers import (
    df_columns_sort_start_end,
    df_sort_by_list,
    styler_highlight_changes,
)
from imxInsights.utils.shapely_geojson import (
    CrsEnum,
    ShapelyGeoJsonFeature,
    ShapelyGeoJsonFeatureCollection,
)
from imxInsights.utils.shapely_transform import ShapelyTransform


class ImxCompareMultiRepo:
    """
    A class for comparing IMX objects across multiple repositories.

    TODO: THIS SHOULD ACT MORE LIKE A NORMAL IMX REPO

    Attributes:
        _data (dict[str, Any]): Internal data dictionary for storing comparison results.
        container_order (Any): Order of containers to consider in the comparison.
        diff (dict[str, list[imxInsights.compare.changedImxObject.ChangedImxObject]]): Dictionary holding the differences.
        _containers (list): List of containers involved in the comparison.
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self.container_order: tuple[str, ...] = ()
        self.diff: dict[str, list[ChangedImxObject]] = {}
        self._containers: list[Any] = []

    @staticmethod
    def _is_priority_field(field: str) -> bool:
        return field in ("@name", "@puic")

    @staticmethod
    def _get_all_properties_keys(
        imx_obj: list[Any], add_extension_objects: bool = True
    ) -> list[str]:
        all_keys = set()
        for d in imx_obj:
            all_keys.update(d.properties.keys())
            all_keys.update(
                d.extension_properties.keys()
            ) if add_extension_objects else None
        return sorted(all_keys)

    def _sort_priority_keys(self, all_keys: list[str]) -> list[str]:
        priority_keys = [field for field in all_keys if self._is_priority_field(field)]
        non_priority_keys = [
            field for field in all_keys if not self._is_priority_field(field)
        ]
        return priority_keys + non_priority_keys

    @staticmethod
    def _get_container_properties(imx_obj: list[Any]) -> dict[str, dict]:
        return {d.container_id: d.properties for d in imx_obj}

    @staticmethod
    def _get_container_extension_properties(imx_obj: list[Any]) -> dict[str, dict]:
        return {d.container_id: d.extension_properties for d in imx_obj}

    @staticmethod
    def _populate_diff(all_keys, container_properties, container_order):
        merged_dict: dict[str, dict] = {key: {} for key in all_keys}
        for key in all_keys:
            for container_id in container_order:
                merged_dict[key][container_id] = container_properties.get(
                    container_id, {}
                ).get(key, None)
        return merged_dict

    @staticmethod
    def _get_merged_properties(
        container_properties: dict[str, dict], extension_properties: dict[str, dict]
    ) -> dict[str, dict]:
        return {
            key: value | extension_properties.get(key, {})
            for key, value in container_properties.items()
        }

    def _set_diff_dict(self, tree):
        """
        Create a dictionary representing the differences between IMX objects.

        Args:
            tree (Any): A tree structure containing IMX objects.

        Returns:
            dict[str, Any]: A dictionary containing the diff results.
        """
        out = {}

        for imx_obj in tree.get_all():
            sorted_keys = self._sort_priority_keys(
                self._get_all_properties_keys(imx_obj)
            )
            properties = self._get_merged_properties(
                self._get_container_properties(imx_obj),
                self._get_container_extension_properties(imx_obj),
            )

            merged_dict = self._populate_diff(
                sorted_keys, properties, self.container_order
            )

            # create empty dicts
            geometry_dict: dict[str, Any] = {
                item: None for item in self.container_order
            }
            tag_dict: dict[str, Any] = {item: None for item in self.container_order}
            children_dict: dict[str, Any] = {
                item: None for item in self.container_order
            }
            parent_dict: dict[str, Any] = {item: None for item in self.container_order}
            # fill dicts
            for item in imx_obj:
                tag_dict[item.container_id] = item.path
                children_dict[item.container_id] = [
                    _.puic for _ in sorted(item.children, key=lambda x: x.puic)
                ]
                parent_dict[item.container_id] = (
                    item.parent.puic if item.parent is not None else None
                )
                geometry_dict[item.container_id] = item.geometry

            merged_dict["tag"] = tag_dict
            merged_dict["parentRef"] = parent_dict
            merged_dict["_geometry"] = geometry_dict
            # TODO: Ensure that if 'parent' is the same as '@puic', it's set to None. uhh why?
            merged_dict["childrenRefs"] = {
                key: " ".join(value) if value is not None else None
                for key, value in children_dict.items()
            }

            out[imx_obj[0].puic] = merged_dict

        self._data = out

    @staticmethod
    def _determine_object_overall_status(diff_dict) -> ChangeStatus:
        unique_statuses = set(
            [value.status for key, value in diff_dict.items() if key != "parentRef"]
        )
        if unique_statuses == {ChangeStatus.UNCHANGED}:
            return ChangeStatus.UNCHANGED
        elif unique_statuses == {ChangeStatus.ADDED}:
            return ChangeStatus.ADDED
        elif unique_statuses == {ChangeStatus.REMOVED}:
            return ChangeStatus.REMOVED
        else:
            return ChangeStatus.CHANGED

    def _set_diff(self, container_id_1, container_id_2):
        with tqdm(total=len(self._data.items()), file=sys.stdout) as pbar:  # type: ignore
            for key, value in self._data.items():
                current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
                pbar.set_description(
                    f"{current_time} | {logger.level('INFO').name}     | comparing"
                )

                tags = {item for item in value["tag"].values() if item is not None}
                tag = tags.pop() if tags else "unknown"

                if tag not in self.diff.keys():
                    self.diff[tag] = []

                dict_1 = {
                    key_2: value_2[container_id_1] for key_2, value_2 in value.items()
                }
                geometry_1 = dict_1["_geometry"]
                del dict_1["_geometry"]
                dict_2 = {
                    key_2: value_2[container_id_2] for key_2, value_2 in value.items()
                }
                geometry_2 = dict_2["_geometry"]
                del dict_2["_geometry"]

                dict_1_flat = remove_empty_dicts(
                    parse_dict_to_value_objects(transform_dict(dict_1))
                )
                dict_2_flat = remove_empty_dicts(
                    parse_dict_to_value_objects(transform_dict(dict_2))
                )

                diff_dict = get_object_changes(dict_1_flat, dict_2_flat)

                change_obj = ChangedImxObject(
                    puic=key,
                    status=self._determine_object_overall_status(diff_dict),
                    changes=diff_dict,
                    geometry=GeometryChange(t1=geometry_1, t2=geometry_2),
                )

                self.diff[tag].append(change_obj)
                pbar.update(1)
        logger.success("Compair done")

    def get_object_types(self) -> list[str]:
        dict_lower_case_merged = merge_dict_keep_first_key(self.diff)
        return sorted(dict_lower_case_merged.keys())

    def get_pandas(
        self,
        object_type: str | None = None,
        add_analyse: bool = False,
        styled_df: bool = False,
    ) -> pd.DataFrame | dict[str, pd.DataFrame]:
        dict_lower_case_merged = merge_dict_keep_first_key(self.diff)

        # If an object_type is specified, get its DataFrame; otherwise, get all DataFrames
        if object_type:
            return self._get_dataframe_for_path(
                dict_lower_case_merged, object_type, add_analyse, styled_df
            )
        else:
            return self._get_all_dataframes(
                dict_lower_case_merged, add_analyse, styled_df
            )

    def _get_all_dataframes(
        self,
        dict_lower_case_merged: dict[str, list],
        add_analyse: bool,
        styled_df: bool,
    ) -> dict[str, pd.DataFrame]:
        result = {}
        object_types = sorted(dict_lower_case_merged.keys())

        for item in object_types:
            result[item] = self._create_dataframe(
                dict_lower_case_merged[item], add_analyse, styled_df
            )

        return result

    def _get_dataframe_for_path(
        self,
        dict_lower_case_merged: dict[str, list],
        object_type: str,
        add_analyse: bool,
        styled_df: bool,
    ) -> pd.DataFrame:
        if object_type in dict_lower_case_merged:
            return self._create_dataframe(
                dict_lower_case_merged[object_type], add_analyse, styled_df
            )
        else:
            raise ValueError(f"Object type '{object_type}' not found.")  # NOQA TRY003

    @staticmethod
    def _create_dataframe(
        items: list, add_analyse: bool, styled_df: bool
    ) -> pd.DataFrame:
        df = pd.DataFrame([item.get_change_dict(add_analyse) for item in items])

        extension_columns = [col for col in df.columns if col.startswith("extension")]
        columns_to_front = ["tag", "@puic", "status"]
        df = df_columns_sort_start_end(df, columns_to_front, extension_columns)

        status_order = [
            ChangeStatus.ADDED.value,
            ChangeStatus.CHANGED.value,
            ChangeStatus.UNCHANGED.value,
            ChangeStatus.REMOVED.value,
            ChangeStatus.TYPE_CHANGE.value,
        ]
        df = df_sort_by_list(df, status_order)

        columns_to_strip = ["tag", "@puic"]
        for col in columns_to_strip:
            df[col] = df[col].str.replace(r"^[+-]{2}", "", regex=True)

        if styled_df:
            return df.style.map(styler_highlight_changes)  # type: ignore
        else:
            return df

    def create_excel(
        self,
        file_path: str | None = None,
        add_analyse: bool = False,
        styled_df: bool = True,
    ):
        file_path = (
            file_path
            if file_path is not None
            else f'diff_excel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        diff_excel = DiffExcel(
            self, file_path, add_analyse=add_analyse, styled_df=styled_df
        )
        diff_excel.save()

    def get_geojson(
        self,
        object_paths: list[str],
        to_wgs: bool = True,
    ) -> ShapelyGeoJsonFeatureCollection:
        """
        Generate a GeoJSON feature collection for the specified object paths.

        This function creates a list of GeoJSON features from the objects in the
        specified paths.

        Args:
            object_paths: A list of object paths to extract geometry from.
            to_wgs: If True, converts the geometries to WGS84.

        Returns:
            A collection of GeoJSON features.
        """

        features = []
        for path in object_paths:
            for item in self.diff[path]:
                if item.geometry and item.geometry.t2:
                    geometry = item.geometry.t2
                    transformed_geometry = (
                        ShapelyTransform.rd_to_wgs(geometry) if to_wgs else geometry
                    )
                    features.append(
                        ShapelyGeoJsonFeature(
                            geometry_list=[transformed_geometry],
                            properties=item.get_change_dict(add_analyse=True),
                        )
                    )

        return ShapelyGeoJsonFeatureCollection(
            features, CrsEnum.WGS84 if to_wgs else CrsEnum.RD_NEW_NAP
        )

    def create_geojson_files(
        self,
        directory_path: str | Path,
        to_wgs: bool = True,
    ):
        """
        Create GeoJSON files for all objects in the diff dictionary.

        This function generates GeoJSON files for each key in the diff dictionary and
        saves them in the specified directory.

        Args:
            directory_path: The path to the directory where the files will be saved.
            to_wgs: If True, converts the geometries to WGS84.

        """

        for key, value in self.diff.items():
            dir_path = Path(directory_path)
            dir_path.mkdir(parents=True, exist_ok=True)
            geojson_feature_collection = self.get_geojson([key], to_wgs=to_wgs)
            geojson_file_path = dir_path / f"{key}.geojson"
            geojson_feature_collection.to_geojson_file(geojson_file_path)
            logger.success(f"GeoJSON file created and saved at {geojson_file_path}.")

    @classmethod
    def from_multi_repo(
        cls, tree, container_order, containers
    ) -> "ImxCompareMultiRepo":
        logger.info("Compair containers")
        _ = cls()
        _._containers = containers
        _.container_order = container_order
        _._set_diff_dict(tree)
        _._set_diff(container_order[0], container_order[1])
        return _

    # TODO: implement metadata diff overview like normal repo has
