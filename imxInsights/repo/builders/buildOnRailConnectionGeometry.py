from collections import defaultdict
from collections.abc import Callable

from loguru import logger
from lxml.etree import _Element as Element

from imxInsights.domain.imxObject import ImxObject
from imxInsights.domain.onRailConnectionGeometry import (
    RailConnectionInfoFailed,
    RailConnectionPoint,
    RailConnectionProfile,
)


def get_elements_skip_with_puic(element, xml_tag: str) -> list[Element]:
    out: list[Element] = []
    for child in element:
        if "puic" in child.attrib:
            continue
        if child.tag == xml_tag:
            out.append(child)
        out.extend(get_elements_skip_with_puic(child, xml_tag))
    return out


def process_on_rail_connection_geometry(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None], xml_tag: str
) -> None:
    rail_connection_geometry_elements = get_elements_skip_with_puic(
        imx_object.element, xml_tag
    )

    for rail_con_info in rail_connection_geometry_elements:
        rail_con: ImxObject | None = find(rail_con_info.get("railConnectionRef", ""))
        if not rail_con:
            logger.error(
                f"{imx_object.puic} ({imx_object.tag}) RailConnection not present"
            )
            imx_object.on_rail_geometry.append(RailConnectionInfoFailed(rail_con_info))
            return

        at_measure = rail_con_info.get("atMeasure", None)
        from_measure = rail_con_info.get("fromMeasure", None)
        to_measure = rail_con_info.get("toMeasure", None)

        if at_measure is not None and (from_measure is not None or to_measure is not None):
            raise ValueError("If 'atMeasure' is present, 'fromMeasure' and 'toMeasure' must not be present.")

        if at_measure is None and (from_measure is None or to_measure is None):
            raise ValueError("If 'atMeasure' is not present, both 'fromMeasure' and 'toMeasure' must be present.")

        if at_measure:
            imx_object.on_rail_geometry.append(
                RailConnectionPoint(rail_con_info, rail_con)
            )
        else:
            imx_object.on_rail_geometry.append(
                RailConnectionProfile(rail_con_info, rail_con)
            )


def create_rail_connection_info_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            try:
                process_on_rail_connection_geometry(
                    imx_object, find, "{http://www.prorail.nl/IMSpoor}RailConnectionInfo"
                )
            except ValueError as e:
                logger.error(f"{imx_object.puic} ({imx_object.tag}) cant create railConnectionInfo geometry {e}")


def create_track_fragment_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            try:
                process_on_rail_connection_geometry(
                    imx_object, find, "{http://www.prorail.nl/IMSpoor}TrackFragment"
                )
            except ValueError as e:
                logger.error(f"{imx_object.puic} ({imx_object.tag}) cant create TrackFragment geometry {e}")


def create_demarcation_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            try:
                process_on_rail_connection_geometry(
                    imx_object, find, "{http://www.prorail.nl/IMSpoor}DemarcationMarker"
                )
            except ValueError as e:
                logger.error(f"{imx_object.puic} ({imx_object.tag}) cant create DemarcationMarker geometry {e}")


def add_on_rail_connection_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
):
    create_rail_connection_info_geometry(tree_dict, find)
    create_track_fragment_geometry(tree_dict, find)
    create_demarcation_geometry(tree_dict, find)
