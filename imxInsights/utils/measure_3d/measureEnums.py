from enum import Enum


class ProjectionPointPosition(Enum):
    LEFT = "left"
    RIGHT = "right"
    ON_LINE = "on_line"
    UNDEFINED = "undefined"


class ProjectionStatus(Enum):
    PERPENDICULAR = "perpendicular"
    ANGLE = "on_a_angle"
    OVERSHOOT = "overshoot"
    UNDERSHOOT = "undershoot"
    UNDEFINED = "undefined"
