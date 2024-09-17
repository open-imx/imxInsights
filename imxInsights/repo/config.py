from dataclasses import dataclass, field
from typing import Literal, cast, overload

from imxInsights.utils.singleton import SingletonMeta

SupportedImxType = (
    Literal["1.2.4"]
    | Literal["5.0.0"]
    | Literal["10.0.0"]
    | Literal["11.0.0"]
    | Literal["12.0.0"]
)


def get_valid_version(version: str) -> SupportedImxType:
    valid_versions = {"1.2.4", "5.0.0", "10.0.0", "11.0.0", "12.0.0"}
    if version not in valid_versions:
        raise ValueError(f"Invalid version: {version}")  # noqa: TRY003
    return cast(SupportedImxType, version)


class Configuration(metaclass=SingletonMeta):
    """
    Configuration class using SingletonMeta to ensure a single instance.

    Info:
        The class maintains a mapping between IMX versions and their respective
        object type extension classes. The `get_object_type_to_extend_config` method
        fetches the appropriate class based on the provided IMX version and returns
        a dictionary of its non-callable attributes.
    """

    @staticmethod
    @overload
    def get_object_type_to_extend_config(
        imx_version: Literal["1.2.4"],
    ) -> "Imx124ExtensionMapping": ...

    @staticmethod
    @overload
    def get_object_type_to_extend_config(
        imx_version: Literal["5.0.0"],
    ) -> "Imx500ExtensionMapping": ...

    @staticmethod
    @overload
    def get_object_type_to_extend_config(
        imx_version: Literal["10.0.0"],
    ) -> "Imx1000ExtensionMapping": ...

    @staticmethod
    @overload
    def get_object_type_to_extend_config(
        imx_version: Literal["12.0.0"],
    ) -> "Imx1200ExtensionMapping": ...

    @staticmethod
    @overload
    def get_object_type_to_extend_config(
        imx_version: Literal["11.0.0"],
    ) -> "Imx1100ExtensionMapping": ...

    @staticmethod
    def get_object_type_to_extend_config(imx_version: str):
        """
        Retrieves the object type extensions for a specific IMX version.

        Args:
            imx_version: The IMX version string.

        Returns:
            (Imx124ExtensionMapping | Imx500ExtensionMapping | Imx1000ExtensionMapping | Imx1100ExtensionMapping | Imx1200ExtensionMapping): depending on imx version

        """
        version_map = {
            "1.2.4": Imx124ExtensionMapping(),
            "5.0.0": Imx500ExtensionMapping(),
            "10.0.0": Imx1000ExtensionMapping(),
            "11.0.0": Imx1100ExtensionMapping(),
            "12.0.0": Imx1200ExtensionMapping(),
        }

        object_type_class = version_map.get(imx_version)

        if object_type_class is None:
            return None
        return object_type_class


@dataclass(frozen=True)
class Imx124ExtensionMapping:
    """
    Contains frozen object extensions mapping specific to IMX version 1.2.4.

    Attributes:
        MicroNode: Default ```[@junctionRef]```.
        MicroLink: Default ```[@railConnectionRef]```.
        FlankProtectionConfiguration: Default ```[@switchMechanismRef, @position]```.
    """

    MicroNode: list[str] = field(default_factory=lambda: ["@junctionRef"])
    MicroLink: list[str] = field(default_factory=lambda: ["@railConnectionRef"])
    FlankProtectionConfiguration: list[str] = field(
        default_factory=lambda: [
            "@switchMechanismRef",
            "@position",
        ]
    )


@dataclass(frozen=True)
class Imx500ExtensionMapping:
    """
    Contains object type extensions specific to IMX version 5.0.0.

    Attributes:
        MicroNode: Default is ```["@junctionRef"]```.
        MicroLink: Default is ```["@implementationObjectRef"]```.
        ConditionNotification: Default is ```["@objectRef"]```.
        ErtmsLevelCrossing: Default is ```["@levelCrossingRef"]```.
        ErtmsSignal: Default is ```["@signalRef"]```.
        ErtmsBaliseGroup: Default is ```["@baliseGroupRef"]```.
        ErtmsRoute: Default is ```["@signalingRouteRef"]```.
        FlankProtectionConfiguration: Default ```[@switchMechanismRef, @position]```.
    """

    MicroNode: list[str] = field(default_factory=lambda: ["@junctionRef"])
    MicroLink: list[str] = field(default_factory=lambda: ["@implementationObjectRef"])
    ConditionNotification: list[str] = field(default_factory=lambda: ["@objectRef"])
    ErtmsLevelCrossing: list[str] = field(default_factory=lambda: ["@levelCrossingRef"])
    ErtmsSignal: list[str] = field(default_factory=lambda: ["@signalRef"])
    ErtmsBaliseGroup: list[str] = field(default_factory=lambda: ["@baliseGroupRef"])
    ErtmsRoute: list[str] = field(default_factory=lambda: ["@signalingRouteRef"])
    FlankProtectionConfiguration: list[str] = field(
        default_factory=lambda: [
            "@switchMechanismRef",
            "@position",
        ]
    )


@dataclass(frozen=True)
class Imx1000ExtensionMapping:
    """
    Contains object type extensions specific to IMX version 10.0.0.

    Attributes:
        MicroNode: Default is ```["@junctionRef"]```.
        MicroLink: Default is ```["@implementationObjectRef"]```.
        ConditionNotification: Default is ```["@objectRef"]```.
        ErtmsLevelCrossing: Default is ```["@levelCrossingRef"]```.
        ErtmsSignal: Default is ```["@signalRef"]```.
        ErtmsBaliseGroup: Default is ```["@baliseGroupRef"]```.
        ErtmsRoute: Default is ```["@functionalRouteRef"]```.
        FlankProtectionConfiguration: Default is ```["@switchMechanismRef", "@switchPosition"]```.
    """

    MicroNode: list[str] = field(default_factory=lambda: ["@junctionRef"])
    MicroLink: list[str] = field(default_factory=lambda: ["@implementationObjectRef"])
    ConditionNotification: list[str] = field(default_factory=lambda: ["@objectRef"])
    ErtmsLevelCrossing: list[str] = field(default_factory=lambda: ["@levelCrossingRef"])
    ErtmsSignal: list[str] = field(default_factory=lambda: ["@signalRef"])
    ErtmsBaliseGroup: list[str] = field(default_factory=lambda: ["@baliseGroupRef"])
    ErtmsRoute: list[str] = field(default_factory=lambda: ["@functionalRouteRef"])
    FlankProtectionConfiguration: list[str] = field(
        default_factory=lambda: ["@switchMechanismRef", "@switchPosition"]
    )


@dataclass(frozen=True)
class Imx1100ExtensionMapping:
    """
    Contains object type extensions specific to IMX version 11.0.0.

    Attributes:
        MicroNode: Default is ```["@junctionRef"]```.
        MicroLink: Default is ```["@implementationObjectRef"]```.
        ConditionNotification: Default is ```["@objectRef"]```.
        ErtmsLevelCrossing: Default is ```["@levelCrossingRef"]```.
        ErtmsSignal: Default is ```["@signalRef"]```.
        ErtmsBaliseGroup: Default is ```["@baliseGroupRef"]```.
        ErtmsRoute: Default is ```["@functionalRouteRef"]```.
    """

    MicroNode: list[str] = field(default_factory=lambda: ["@junctionRef"])
    MicroLink: list[str] = field(default_factory=lambda: ["@implementationObjectRef"])
    ConditionNotification: list[str] = field(default_factory=lambda: ["@objectRef"])
    ErtmsLevelCrossing: list[str] = field(default_factory=lambda: ["@levelCrossingRef"])
    ErtmsSignal: list[str] = field(default_factory=lambda: ["@signalRef"])
    ErtmsBaliseGroup: list[str] = field(default_factory=lambda: ["@baliseGroupRef"])
    ErtmsRoute: list[str] = field(default_factory=lambda: ["@functionalRouteRef"])


@dataclass(frozen=True)
class Imx1200ExtensionMapping:
    """
    Contains object type extensions specific to IMX version 12.0.0.

    Attributes:
        MicroNode: Default is ```["@junctionRef"]```.
        MicroLink: Default is ```["@implementationObjectRef"]```.
        ConditionNotification: Default is ```["@objectRef"]```.
        ErtmsLevelCrossing: Default is ```["@levelCrossingRef"]```.
        ErtmsSignal: Default is ```["@signalRef"]```.
        ErtmsBaliseGroup: Default is ```["@baliseGroupRef"]```.
        ErtmsRoute: Default is ```["@functionalRouteRef"]```.
        ObservedLocation: Default is ```["@objectRef"]```.
    """

    MicroNode: list[str] = field(default_factory=lambda: ["@junctionRef"])
    MicroLink: list[str] = field(default_factory=lambda: ["@implementationObjectRef"])
    ConditionNotification: list[str] = field(default_factory=lambda: ["@objectRef"])
    ErtmsLevelCrossing: list[str] = field(default_factory=lambda: ["@levelCrossingRef"])
    ErtmsSignal: list[str] = field(default_factory=lambda: ["@signalRef"])
    ErtmsBaliseGroup: list[str] = field(default_factory=lambda: ["@baliseGroupRef"])
    ErtmsRoute: list[str] = field(default_factory=lambda: ["@functionalRouteRef"])
    ObservedLocation: list[str] = field(default_factory=lambda: ["@objectRef"])
