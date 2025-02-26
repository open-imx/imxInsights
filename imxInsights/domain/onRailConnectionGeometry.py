from dataclasses import dataclass, field

import numpy as np
from lxml.etree import _Element as Element
from shapely import LineString, Point

from imxInsights.domain.imxObject import ImxObject
from imxInsights.utils.shapely.shapley_helpers import (
    cut_profile,
    get_azimuth_from_points,
    reverse_line,
)


# TODO: remove exceptions!

class RailConnectionInfoException(Exception):
    """Something is wrong shit the railConnectionInfo"""

    def __init__(self, message="An error occurred"):
        super().__init__(message)
        self.message = message


@dataclass
class RailConnectionInfoFailed:
    _element: Element


@dataclass
class RailConnectionPoint:
    _element: Element
    _rail_connection: ImxObject

    rail_con_ref: str | None = field(init=False, default=None)
    at_measure: float | None = field(init=False, default=None)
    direction: str | None = field(init=False, default=None)

    geometry: Point = field(init=False, default_factory=Point)
    azimuth: float = field(init=False, default=np.nan)

    def __post_init__(self):
        self.rail_con_ref = self._element.get("railConnectionRef")
        self.at_measure = float(self._element.get("atMeasure", np.nan))
        self.direction = self._element.get("direction")

        if np.isnan(self.at_measure):
            raise RailConnectionInfoException(
                f"measures issue atMeasure: {self.at_measure}"
            )

        self.geometry = self._rail_connection.geometry.interpolate(self.at_measure)
        if self.direction == "Upstream":
            point_in_direction = self._rail_connection.geometry.interpolate(
                self.at_measure - 1
            )
        elif self.direction == "Downstream":
            point_in_direction = self._rail_connection.geometry.interpolate(
                self.at_measure + 1
            )
        elif self.direction == "None":
            point_in_direction = self.geometry
        elif self.direction == "Unknown":
            point_in_direction = self.geometry
        else:
            raise ValueError("Missing info")

        if point_in_direction:
            self.azimuth = get_azimuth_from_points(self.geometry, point_in_direction)


@dataclass
class RailConnectionProfile:
    _element: Element
    _rail_connection: ImxObject

    rail_con_ref: str | None = field(init=False, default=None)
    from_measure: float | None = field(init=False, default=None)
    to_measure: float | None = field(init=False, default=None)
    direction: str | None = field(init=False, default=None)

    geometry: LineString = field(init=False, default_factory=LineString)

    def __post_init__(self):
        self.rail_con_ref = self._element.get("railConnectionRef")
        self.from_measure = float(self._element.get("fromMeasure", np.nan))
        self.to_measure = float(self._element.get("toMeasure", np.nan))
        self.direction = self._element.get("direction")
        if np.isnan(self.from_measure) or np.isnan(self.to_measure):
            raise RailConnectionInfoException(
                f"measures issue fromMeasure: {self.from_measure} toMeasure={self.to_measure}"
            )
        if not isinstance(self._rail_connection.geometry, LineString):
            raise RailConnectionInfoException(
                "RailConnection geometry is not a Linestring"
            )
        self.geometry = cut_profile(
            self._rail_connection.geometry, self.from_measure, self.to_measure
        )
        from_point = self._rail_connection.geometry.interpolate(self.from_measure)
        to_point = self._rail_connection.geometry.interpolate(self.to_measure)
        if Point(self.geometry.coords[0]).distance(from_point) > Point(
            self.geometry.coords[0]
        ).distance(to_point):
            self.geometry = reverse_line(self.geometry)
