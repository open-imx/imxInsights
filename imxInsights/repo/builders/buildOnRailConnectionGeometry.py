from collections import defaultdict
from collections.abc import Callable

from loguru import logger
from lxml.etree import _Element as Element

from imxInsights.domain.imxObject import ImxObject
from imxInsights.domain.onRailConnectionGeometry import (
    RailConnectionInfoException,
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
        try:
            if at_measure:
                imx_object.on_rail_geometry.append(
                    RailConnectionPoint(rail_con_info, rail_con)
                )
            else:
                imx_object.on_rail_geometry.append(
                    RailConnectionProfile(rail_con_info, rail_con)
                )

        except RailConnectionInfoException as e:
            logger.error(f"{imx_object.puic} ({imx_object.tag}) {e}")
            imx_object.on_rail_geometry.append(RailConnectionInfoFailed(rail_con_info))


def create_rail_connection_info_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            process_on_rail_connection_geometry(
                imx_object, find, "{http://www.prorail.nl/IMSpoor}RailConnectionInfo"
            )


def create_track_fragment_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            process_on_rail_connection_geometry(
                imx_object, find, "{http://www.prorail.nl/IMSpoor}TrackFragment"
            )


def create_demarcation_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            process_on_rail_connection_geometry(
                imx_object, find, "{http://www.prorail.nl/IMSpoor}DemarcationMarker"
            )


def add_on_rail_connection_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
):
    create_rail_connection_info_geometry(tree_dict, find)
    create_track_fragment_geometry(tree_dict, find)
    create_demarcation_geometry(tree_dict, find)
