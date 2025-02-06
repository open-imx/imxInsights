from dataclasses import dataclass, field

from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from imxInsights.compare.changes import Change, get_object_changes
from imxInsights.compare.changeStatusEnum import ChangeStatusEnum
from imxInsights.compare.geometryChange import GeometryChange
from imxInsights.domain.imxObject import ImxObject
from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeature
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform


@dataclass
class ChangedImxObject:
    t1: ImxObject | None
    t2: ImxObject | None
    puic: str = field(init=False)
    changes: dict[str, Change] = field(init=False)
    status: ChangeStatusEnum = field(init=False)
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
        raise ValueError("PUIC is required but not found in t1 or t2.")

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

    def _determine_object_overall_status(self) -> ChangeStatusEnum:
        unique_statuses = {
            change.status for key, change in self.changes.items() if key != "parentRef"
        }
        if unique_statuses in [{ChangeStatusEnum.UNCHANGED}, set()]:
            return ChangeStatusEnum.UNCHANGED
        elif unique_statuses == {ChangeStatusEnum.ADDED}:
            return ChangeStatusEnum.ADDED
        elif unique_statuses == {ChangeStatusEnum.REMOVED}:
            return ChangeStatusEnum.REMOVED
        else:
            return ChangeStatusEnum.CHANGED

    def _initialize_geometry(self) -> GeometryChange | None:
        return GeometryChange(
            t1=self.t1.geometry if self.t1 else None,
            t2=self.t2.geometry if self.t2 else None,
        )

    def get_change_dict(self, add_analyse: bool = False) -> dict[str, str]:
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
            | {
                "status": self.status.value,
                "geometry_status": self.geometry.status.value if self.geometry else "",
            }
        )

    def as_geojson_feature(
        self, add_analyse: bool = False, as_wgs: bool = True
    ) -> ShapelyGeoJsonFeature:
        geometry = []

        if self.geometry:
            selected_geometry = (
                self.geometry.t2 if self.geometry.t2 is not None else self.geometry.t1
            )
            if selected_geometry:
                geometry.append(selected_geometry)

        geometry = [
            item
            for item in geometry
            if item is not None and item.wkt != "GEOMETRYCOLLECTION EMPTY"
        ]

        if as_wgs:
            geometry = [
                ShapelyTransform.rd_to_wgs(_) for _ in geometry if _ is not None
            ]

        geometry = [
            g
            for g in geometry
            if isinstance(
                g,
                (
                    Point
                    | LineString
                    | Polygon
                    | MultiPoint
                    | MultiLineString
                    | MultiPolygon
                    | GeometryCollection
                ),
            )
        ]

        return ShapelyGeoJsonFeature(
            geometry, properties=dict(sorted(self.get_change_dict(add_analyse).items()))
        )
