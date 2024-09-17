from enum import Enum


class ImxSituationEnum(str, Enum):
    """Valid situations in a imx project file."""

    InitialSituation = "InitialSituation"
    """The initial situation in a imx project file."""

    NewSituation = "NewSituation"
    """ The initial situation in a imx project file."""

    Situation = "Situation"
    """A situation in a imx situation file."""
