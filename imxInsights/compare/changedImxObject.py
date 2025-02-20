from shapely.geometry import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)

from imxInsights.compare.changes import get_object_changes
from imxInsights.compare.changeStatusEnum import ChangeStatusEnum
from imxInsights.compare.geometryChange import GeometryChange
from imxInsights.domain.imxObject import ImxObject
from imxInsights.utils.shapely.shapely_geojson import ShapelyGeoJsonFeature
from imxInsights.utils.shapely.shapely_transform import ShapelyTransform


class ChangedImxObject:
    def __init__(self, t1: ImxObject | None, t2: ImxObject | None):
        """Represents a changed IMX object by comparing two versions (t1 and t2).

        Args:
            t1: The first version of the IMX object.
            t2: The second version of the IMX object.
        """
        self.t1 = t1
        self.t2 = t2
        self.puic: str = self._get_puic()

        t1_props, t2_props = self._prepare_properties()
        self.changes = get_object_changes(t1_props, t2_props)
        self.status = self._determine_object_overall_status()
        self.geometry = self._initialize_geometry()

    @property
    def tag(self) -> str:
        """Gets the tag of the changed object.

        Returns:
            The diff string of the tag change.
        """
        return self.changes["tag"].diff_string

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
        """Generates a dictionary representing the changes.

        Args:
            add_analyse: Whether to include analysis information.

        Returns:
            A dictionary mapping property names to their change representations.
        """
        analyse = (
            {
                f"{key}|analyse": "\n".join(value.analyse["display"].split(" "))
                if value.analyse["type"] == "UUIDListOperator"
                else value.analyse["display"]
                for key, value in self.changes.items()
                if value.analyse is not None
            }
            if add_analyse
            else {}
        )

        response = (
            {key: value.diff_string for key, value in self.changes.items()}
            | analyse
            | {
                "status": self.status.value,
                "geometry_status": self.geometry.status.value if self.geometry else "",
            }
        )

        return response

    def as_geojson_feature(
        self, add_analyse: bool = True, as_wgs: bool = True
    ) -> ShapelyGeoJsonFeature:
        """Converts the changed object to a GeoJSON feature.

        Args:
            add_analyse: Whether to include analysis information.
            as_wgs: Whether to transform the geometry to WGS coordinates.

        Returns:
            A ShapelyGeoJsonFeature representing the object.
        """
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
