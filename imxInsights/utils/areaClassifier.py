from collections.abc import Callable, Iterable
from dataclasses import dataclass
from typing import (
    Any,
    Generic,
    Literal,
    Protocol,
    TypeVar,
    runtime_checkable,
)

from shapely.geometry import base
from shapely.strtree import STRtree

TreeQueryRelation = Literal[
    "intersects",
    "within",
    "overlaps",
    "crosses",
    "touches",
    "covers",
    "covered_by",
    "contains_properly",
]


@runtime_checkable
class AreaLike(Protocol):
    name: str | None
    shapely: base.BaseGeometry


TArea = TypeVar("TArea", bound=AreaLike)


@dataclass(frozen=True)
class AreaHit(Generic[TArea]):
    area_index: int
    area: TArea
    relation: TreeQueryRelation


class AreaClassifier(Generic[TArea]):
    def __init__(self, areas: Iterable[TArea]) -> None:
        self._areas: list[TArea] = list(areas or [])
        self._geoms: list[base.BaseGeometry] = [item.shapely for item in self._areas]
        self._tree: STRtree = STRtree(self._geoms)

    @property
    def areas(self) -> list[TArea]:
        return self._areas

    def classify(
        self,
        obj: Any,
        *,
        relation: TreeQueryRelation = "intersects",
        geometry_getter: Callable[[Any], base.BaseGeometry] | None = None,
    ) -> list[AreaHit[TArea]]:
        if not self._areas:
            return []
        geom = self._get_geometry(obj, geometry_getter)
        indices = self._tree.query(geom, predicate=relation)
        return [AreaHit(i, self._areas[i], relation) for i in map(int, indices)]

    def classify_many(
        self,
        objs: Iterable[Any],
        *,
        relation: TreeQueryRelation = "intersects",
        geometry_getter: Callable[[Any], base.BaseGeometry] | None = None,
    ) -> list[list[AreaHit[TArea]]]:
        objs_list = list(objs)
        if not objs_list or not self._areas:
            return [[] for _ in objs_list]

        geoms = [self._get_geometry(o, geometry_getter) for o in objs_list]
        pairs = self._tree.query(geoms, predicate=relation)
        hits_per_obj: list[list[AreaHit[TArea]]] = [[] for _ in objs_list]
        if len(pairs) == 0:
            return hits_per_obj

        input_idx_arr, area_idx_arr = pairs[0], pairs[1]
        for in_idx, area_idx in zip(map(int, input_idx_arr), map(int, area_idx_arr)):
            area = self._areas[area_idx]
            hits_per_obj[in_idx].append(AreaHit(area_idx, area, relation))
        return hits_per_obj

    @staticmethod
    def _get_geometry(
        obj: Any,
        geometry_getter: Callable[[Any], base.BaseGeometry] | None,
    ) -> base.BaseGeometry:
        if geometry_getter is not None:
            return geometry_getter(obj)
        if isinstance(obj, base.BaseGeometry):
            return obj
        if hasattr(obj, "geometry"):
            return getattr(obj, "geometry")
        raise AttributeError(
            "Object must be a Shapely geometry or provide a .geometry attribute."
        )

    def flags_by_name(
        self,
        obj: Any,
        *,
        relation: TreeQueryRelation = "intersects",
        geometry_getter: Callable[[Any], base.BaseGeometry] | None = None,
    ) -> dict[str, bool]:
        hits = self.classify(obj, relation=relation, geometry_getter=geometry_getter)
        names = {a.name for a in self._areas if a.name is not None}
        return {n: any(h.area.name == n for h in hits) for n in names}
