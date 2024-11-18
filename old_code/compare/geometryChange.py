# from dataclasses import dataclass, field
# from enum import Enum
#
# from shapely import (
#     GeometryCollection,
#     LineString,
#     MultiLineString,
#     MultiPoint,
#     MultiPolygon,
#     Point,
#     Polygon,
# )
#
#
# class GeometryChangeStatus(Enum):
#     """
#     Enum for representing different types of changes.
#     """
#
#     UNDEFINED = "undefined"
#     ADDED = "added"
#     REMOVED = "removed"
#     UNCHANGED = "unchanged"
#     CHANGED = "changed"
#     Z_ADDED = "Z_ADDED"
#
#
# @dataclass
# class GeometryChange:
#     t1: (
#         Point
#         | LineString
#         | Polygon
#         | GeometryCollection
#         | MultiPoint
#         | MultiLineString
#         | MultiPolygon
#         | None
#     ) = None
#     t2: (
#         Point
#         | LineString
#         | Polygon
#         | GeometryCollection
#         | MultiPoint
#         | MultiLineString
#         | MultiPolygon
#         | None
#     ) = None
#     status: GeometryChangeStatus = field(init=False)
#
#     def __post_init__(self):
#         # TODO: set status based on the geometry diff
#         self.status = GeometryChangeStatus.UNDEFINED
