from dataclasses import dataclass, field
from enum import Enum

from shapely import (
    GeometryCollection,
    LineString,
    MultiLineString,
    MultiPoint,
    MultiPolygon,
    Point,
    Polygon,
)
from shapely.geometry.base import BaseGeometry

from imxInsights.utils.shapely.shapley_helpers import compute_geometry_movement


class GeometryChangeStatus(Enum):
    """
    Enum for representing different types of changes.
    """

    UNDEFINED = "undefined"
    ADDED = "added"
    REMOVED = "removed"
    UNCHANGED = "unchanged"
    CHANGED = "changed"
    Z_ADDED = "Z_added"
    Z_REMOVED = "Z_removed"
    Z_CHANGED = "Z_changed"


@dataclass
class GeometryChange:
    t1: (
        Point
        | LineString
        | Polygon
        | GeometryCollection
        | MultiPoint
        | MultiLineString
        | MultiPolygon
        | None
    ) = None
    t2: (
        Point
        | LineString
        | Polygon
        | GeometryCollection
        | MultiPoint
        | MultiLineString
        | MultiPolygon
        | None
    ) = None
    status: GeometryChangeStatus = field(init=False)

    def __post_init__(self):
        self.status = self._determine_status()

    def _determine_status(self) -> GeometryChangeStatus:
        if (self.t1 is None or self.t1.wkt == "GEOMETRYCOLLECTION EMPTY") and (
            self.t2 is None or self.t2.wkt == "GEOMETRYCOLLECTION EMPTY"
        ):
            return GeometryChangeStatus.UNDEFINED
        elif not self.t2:
            return GeometryChangeStatus.REMOVED
        elif not self.t1:
            return GeometryChangeStatus.ADDED
        if self._is_equal_2d(self.t1, self.t2):
            if not self.t1.has_z and self.t2.has_z:
                return GeometryChangeStatus.Z_ADDED
            elif not self.t2.has_z and self.t1.has_z:
                return GeometryChangeStatus.Z_REMOVED

            if self._has_different_z(self.t1, self.t2):
                return GeometryChangeStatus.Z_CHANGED
            else:
                return GeometryChangeStatus.UNCHANGED
        else:
            return GeometryChangeStatus.CHANGED

    @staticmethod
    def _is_equal_2d(geom1: BaseGeometry, geom2: BaseGeometry) -> bool:
        return geom1.equals_exact(geom2, tolerance=0)

    @staticmethod
    def _has_different_z(geom1: BaseGeometry, geom2: BaseGeometry) -> bool:
        """Check if two geometries have different Z coordinates."""
        if geom1.geom_type != geom2.geom_type:
            return True

        if isinstance(geom1, Polygon) and isinstance(geom2, Polygon):
            coords1 = [geom1.exterior.coords] + [
                interior.coords for interior in geom1.interiors
            ]
            coords2 = [geom2.exterior.coords] + [
                interior.coords for interior in geom2.interiors
            ]
        else:
            coords1 = [geom1.coords]
            coords2 = [geom2.coords]

        if len(coords1) != len(coords2):
            return True

        for ring1, ring2 in zip(coords1, coords2):
            if len(ring1) != len(ring2):
                return True
            for coord1, coord2 in zip(ring1, ring2):
                if len(coord1) > 2:
                    z1 = coord1[2]
                else:
                    z1 = None

                if len(coord2) > 2:
                    z2 = coord2[2]
                else:
                    z2 = None

                if z1 != z2:
                    return True

        return False

    def geometry_movement(self):
        # todo: add return type, ad default return value
        if self.t1 and self.t2:
            return compute_geometry_movement(self.t1, self.t2)
