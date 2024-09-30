from dataclasses import dataclass
from datetime import datetime
from typing import Any

from imxInsights.compair.changes import Change, ChangeStatus, get_changes
from imxInsights.compair.excelReportGenerator import ExcelReportGenerator
from imxInsights.compair.helpers import (
    parse_dict_to_value_objects,
    remove_empty_dicts,
    transform_dict,
)
from loguru import logger
from tqdm import tqdm
import sys



@dataclass
class ChangedImxObject:
    """
    Represents a changed IMX object with its change status and details.

    Attributes:
        puic (str): The unique identifier of the IMX object.
        status (ChangeStatus): The change status of the IMX object.
        changes (dict[str, Change]): A dictionary of changes for the IMX object.
    """

    puic: str
    status: ChangeStatus
    changes: dict[str, Change]

    def get_change_dict(self) -> dict[str, str]:
        """
        Get a dictionary representation of the changes.

        Returns:
            A dictionary with change details and status.
        """
        return {key: value.diff_string for key, value in self.changes.items()} | {
            "status": self.status.value
        }


class ImxCompareMultiRepo:
    """
    A class for comparing IMX objects across multiple repositories.

    Attributes:
        _data (dict[str, Any]): Internal data dictionary for storing comparison results.
        container_order (Any): Order of containers to consider in the comparison.
        diff (dict[str, list[ChangedImxObject]]): Dictionary holding the differences.
        _containers (list): List of containers involved in the comparison.
    """

    def __init__(self):
        self._data: dict[str, Any] = {}
        self.container_order: Any = ()
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

            tag_dict: dict[str, Any] = {item: None for item in self.container_order}
            children_dict: dict[str, Any] = {
                item: None for item in self.container_order
            }
            parent_dict: dict[str, Any] = {item: None for item in self.container_order}

            for item in imx_obj:
                tag_dict[item.container_id] = item.path
                children_dict[item.container_id] = [
                    _.puic for _ in sorted(item.children, key=lambda x: x.puic)
                ]
                parent_dict[item.container_id] = (
                    item.parent.puic if item.parent is not None else None
                )

            merged_dict["tag"] = tag_dict
            merged_dict["parent"] = parent_dict

            # TODO: Ensure that if 'parent' is the same as '@puic', it's set to None. uhh why?
            merged_dict["children"] = children_dict

            out[imx_obj[0].puic] = merged_dict

        self._data = out

    @staticmethod
    def determine_overall_status(diff_dict) -> ChangeStatus:
        unique_statuses = set([item.status for item in diff_dict.values()])
        if unique_statuses == {ChangeStatus.UNCHANGED}:
            return ChangeStatus.UNCHANGED
        elif unique_statuses == {ChangeStatus.ADDED}:
            return ChangeStatus.ADDED
        elif unique_statuses == {ChangeStatus.REMOVED}:
            return ChangeStatus.REMOVED
        else:
            return ChangeStatus.CHANGED

    def _set_diff(self, container_id_1, container_id_2):

        with tqdm(total=len(self._data.items()), file=sys.stdout) as pbar:
            for key, value in self._data.items():
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')[:-3]
                pbar.set_description(f"{current_time} | {logger.level('INFO').name}     | processing")

                tags = {item for item in value["tag"].values() if item is not None}
                tag = tags.pop() if tags else None

                if tag not in self.diff.keys():
                    self.diff[tag] = []

                dict_1 = {
                    key_2: value_2[container_id_1] for key_2, value_2 in value.items()
                }
                dict_2 = {
                    key_2: value_2[container_id_2] for key_2, value_2 in value.items()
                }

                dict_1_flat = remove_empty_dicts(
                    parse_dict_to_value_objects(transform_dict(dict_1))
                )
                dict_2_flat = remove_empty_dicts(
                    parse_dict_to_value_objects(transform_dict(dict_2))
                )

                diff_dict = get_changes(dict_1_flat, dict_2_flat)

                self.diff[tag].append(
                    ChangedImxObject(
                        puic=value["@puic"][container_id_1],
                        status=self.determine_overall_status(diff_dict),
                        changes=diff_dict,
                    )
                )

                pbar.update(1)
        logger.success("Compair done")

    def create_excel(self, file_path: str | None = None):
        file_path = (
            file_path or f'diff_excel_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
        report_generator = ExcelReportGenerator(
            self.diff, self._containers, self.container_order
        )
        report_generator.create_excel(file_path)

    @classmethod
    def from_multi_repo(cls, tree, container_order, containers):
        logger.info(f"Compair containers.")
        _ = cls()
        _._containers = containers
        _.container_order = container_order
        _._set_diff_dict(tree)
        _._set_diff(container_order[0], container_order[1])
        return _
