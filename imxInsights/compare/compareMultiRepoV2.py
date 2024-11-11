from collections import OrderedDict
from dataclasses import dataclass, field

import pandas as pd

from imxInsights.compare.changes import Change, ChangeStatus, get_object_changes
from imxInsights.compare.geometryChange import GeometryChange
from imxInsights.domain.imxObject import ImxObject
from imxInsights.file.containerizedImx.imxContainerProtocol import ImxContainerProtocol
from imxInsights.file.singleFileImx.imxSituationProtocol import ImxSituationProtocol


@dataclass
class ChangedImxObjectV2:
    t1: ImxObject | None
    t2: ImxObject | None
    puic: str = field(init=False)
    changes: dict[str, Change] = field(init=False)
    status: ChangeStatus = field(init=False)
    geometry: GeometryChange | None = field(init=False)

    def __post_init__(self):
        self.puic = self._get_puic()
        t1_props, t2_props = self._prepare_properties()
        self.changes = get_object_changes(t1_props, t2_props)
        self.status = self._determine_object_overall_status()
        self.geometry = self._initialize_geometry()

    def _get_puic(self) -> str:
        if self.t1 and hasattr(self.t1, "puic"):
            return self.t1.puic
        elif self.t2 and hasattr(self.t2, "puic"):
            return self.t2.puic
        else:
            raise AttributeError("Neither t1 nor t2 has a 'puic' attribute.")

    def _prepare_properties(self) -> tuple[dict, dict]:
        t1_props = self.t1.get_imx_property_dict() if self.t1 else {}
        t2_props = self.t2.get_imx_property_dict() if self.t2 else {}
        return self._add_missing_keys(t1_props, t2_props)

    @staticmethod
    def _add_missing_keys(dict1: dict, dict2: dict) -> tuple[dict, dict]:
        all_keys = dict1.keys() | dict2.keys()
        for key in all_keys:
            dict1.setdefault(key, None)
            dict2.setdefault(key, None)
        return dict1, dict2

    def _determine_object_overall_status(self) -> ChangeStatus:
        unique_statuses = {
            change.status for key, change in self.changes.items() if key != "parentRef"
        }
        if unique_statuses in [{ChangeStatus.UNCHANGED}, set()]:
            return ChangeStatus.UNCHANGED
        elif unique_statuses == {ChangeStatus.ADDED}:
            return ChangeStatus.ADDED
        elif unique_statuses == {ChangeStatus.REMOVED}:
            return ChangeStatus.REMOVED
        else:
            return ChangeStatus.CHANGED

    def _initialize_geometry(self) -> GeometryChange | None:
        return GeometryChange(
            t1=self.t1.geometry if self.t1 else None,
            t2=self.t2.geometry if self.t2 else None,
        )

    def get_change_dict(self, add_analyse: bool) -> dict[str, str]:
        analyse = (
            {
                f"{key}_analyse": value.analyse["display"]
                for key, value in self.changes.items()
                if value.analyse is not None
            }
            if add_analyse
            else {}
        )

        return (
            {key: value.diff_string for key, value in self.changes.items()}
            | analyse
            | {"status": self.status.value}
        )


class MultiRepoImxObjectV2:
    def __init__(
        self, imx_objects: tuple[ImxObject | None, ...], container_order: list[str]
    ):
        self.imx_objects = imx_objects
        self.container_order: tuple[str, ...] = tuple(container_order)

    def get_by_container_id(self, container_id: str) -> ImxObject | None:
        """Retrieve the ImxObject for a specific container."""
        if container_id not in self.container_order:
            raise ValueError(f"container_id: {container_id} not present")

        container_index = self.container_order.index(container_id)
        return (
            self.imx_objects[container_index]
            if container_index < len(self.imx_objects)
            else None
        )

    @property
    def puic(self) -> str:
        return [_.puic for _ in self.imx_objects if _ is not None][0]

    def __iter__(self):
        for item in self.imx_objects:
            yield item

    def __repr__(self):
        return f"<MultiRepoImxObject {self.imx_objects} >"

    def compare(self, container_id_t1: str, container_id_t2: str) -> ChangedImxObjectV2:
        t1 = self.get_by_container_id(container_id_t1)
        t2 = self.get_by_container_id(container_id_t2)
        return ChangedImxObjectV2(
            t1=t1,
            t2=t2,
        )


class ImxCompareMultiRepoV2:
    def __init__(
        self,
        containers: list[ImxContainerProtocol | ImxSituationProtocol],
        version_safe: bool = True,
    ):
        self._validate_containers(containers, version_safe)
        self._containers: list[ImxContainerProtocol | ImxSituationProtocol] = containers
        self.container_order: list[str] = [
            container.container_id for container in self._containers
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
        for container in self._containers:
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

    def _get_objects_by_key(self, key: str | None = None) -> MultiRepoImxObjectV2:
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
        return MultiRepoImxObjectV2(tester, self.container_order)

    def find(self, key: str, return_none=True) -> MultiRepoImxObjectV2:
        """Returns all ImxObject instances for a given key (puic), maintaining container order."""
        return self._get_objects_by_key(key)

    def get_all(self) -> list[MultiRepoImxObjectV2]:
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

    def get_by_types(self, object_types: list[str]) -> list[MultiRepoImxObjectV2]:
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

    def get_by_paths(self, object_paths: list[str]) -> list[MultiRepoImxObjectV2]:
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
                if imx_obj:
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
    ) -> list[MultiRepoImxObjectV2]:
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


from imxInsights import ImxContainer, ImxSingleFile

imx_a = ImxSingleFile(
    r"C:\Users\marti\OneDrive - ProRail BV\ENL\TVP4\tvp4a_10-24\RVTO Swd-Dz P03\IMX levering ENL Perceel 4A 04-10-2024\O_D_003122_ENL_TVP04a_000__RVTO_20241001.xml"
)
imx_container = ImxContainer(r"C:\repos\imxInsights\sample_data\compare\NewSituation")

multi = ImxCompareMultiRepoV2(
    [
        situation
        for situation in [imx_a.initial_situation, imx_a.new_situation, imx_container]
        if situation is not None
    ],
    version_safe=False,
)
tester_0 = multi.get_all()

tester_1_a = multi.find("3a813351-5b73-4cb2-9882-90fbedafeb97")
tester_1_a_compare = tester_1_a.compare(
    container_id_t1=tester_1_a.container_order[0],
    container_id_t2=tester_1_a.container_order[1],
)


tester_1_b = multi.find("f1e5f05f-deae-48b5-82f4-1746607b1ed4")
tester_1_b_compare = tester_1_b.compare(
    container_id_t1=tester_1_a.container_order[0],
    container_id_t2=tester_1_a.container_order[1],
)


tester_2 = multi.get_all_types()
tester_2_query = multi.get_by_types(["ReflectorPost"])

tester_3 = multi.get_all_paths()
tester_3_query = multi.get_by_paths(["SingleSwitch.SwitchMechanism.Lock"])


df_ = multi.get_pandas_df(paths=["CivilConstruction"], pivot_df=True)
df_.to_excel("tester.xlsx", merge_cells=False)


df_a = multi.get_pandas_df(paths=["AtbVvInstallation"])


df_b = multi.get_pandas_df(
    types=["Signal", "Sign"], paths=["SingleSwitch.SwitchMechanism.Lock"]
)

df_pivot = multi.get_pandas_df(
    types=["Signal", "Sign"], paths=["SingleSwitch.SwitchMechanism.Lock"], pivot_df=True
)


# tester = multi.get_pandas_df_dict()
print()
