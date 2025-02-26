from collections import defaultdict
from typing import Callable

from loguru import logger
from shapely import GeometryCollection, MultiLineString, MultiPoint

from imxInsights.domain.imxObject import ImxObject


def build_ppc_tracks(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version == "1.2.4":
        imx_object.geometry = MultiPoint(
            [
                find(imx_object.properties["@beginDemarcatorRef"]).geometry,
                find(imx_object.properties["@endDemarcatorRef"]).geometry,
            ]
        )
    elif imx_object.imx_file.imx_version == "5.0.0":
        imx_object.geometry = MultiPoint(
            [
                find(imx_object.properties["@demarcatorOneSideRef"]).geometry,
                find(imx_object.properties["@demarcatorOtherSideRef"]).geometry,
            ]
        )
    elif imx_object.imx_file.imx_version == "12.0.0":
        imx_object.geometry = MultiPoint(
            [
                ref.imx_object.geometry
                for ref in imx_object.refs
                if "DemarcationObject" in ref.field
            ]
        )
    else:
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def build_stop_connections(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version == "1.2.4":
        # stop connection is a element of signal.
        pass
    elif imx_object.imx_file.imx_version in ["5.0.0", "12.0.0"]:
        imx_object.geometry = find(imx_object.properties["@signalRef"]).geometry
    else:
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def build_track_circuit(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version in ["1.2.4", "5.0.0"]:
        imx_object.geometry = MultiPoint(
            [
                find(item).geometry
                for item in imx_object.properties["InsulatedJointRefs"].split()
            ]
        )
    elif imx_object.imx_file.imx_version == "12.0.0":
        imx_object.geometry = MultiPoint(
            [
                ref.imx_object.geometry
                for ref in imx_object.refs
                if "DemarcationObject" in ref.field
            ]
        )
    else:
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def build_axle_counter_section(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version in ["1.2.4", "5.0.0"]:
        imx_object.geometry = MultiPoint(
            [
                find(item).geometry
                for item in imx_object.properties[
                    "AxleCounterDetectionPointRefs"
                ].split()
            ]
        )
    elif imx_object.imx_file.imx_version == "12.0.0":
        imx_object.geometry = MultiPoint(
            [
                ref.imx_object.geometry
                for ref in imx_object.refs
                if "DemarcationObject" in ref.field
            ]
        )
    else:
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def build_work_zones(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version in ["1.2.4", "5.0.0"]:
        multipoints = [
            find(item).geometry for item in imx_object.properties["SectionRefs"].split()
        ]
        merged_multipoint = MultiPoint([pt for mp in multipoints for pt in mp.geoms])
        imx_object.geometry = merged_multipoint
    elif imx_object.imx_file.imx_version == "12.0.0":
        imx_object.geometry = MultiLineString(
            [item.geometry for item in imx_object.on_rail_geometry]
        )
    else:
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def build_temporary_shunting_areas(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    if imx_object.imx_file.imx_version in ["1.2.4", "5.0.0"]:
        points = [
            find(item).geometry
            for item in imx_object.properties["DemarcationRefs"].split()
        ]
        imx_object.geometry = MultiPoint(points)
    elif imx_object.imx_file.imx_version == "12.0.0":
        logger.warning(
            f"{imx_object.tag} IMX {imx_object.imx_file.imx_version} haz no geometry builder!"
        )


def add_specific_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
):
    # TODO: CREATE GEOMETRY COLLECTION if lines and points !!!
    # TODO: WHAT TO DO WHIT FlankProtectionConfiguration (geometry collection?

    second_process_list = []
    for key, imx_objects in tree_dict.items():
        for imx_object in imx_objects:
            if imx_object.tag in ["PPCTrack", "PpcTrack"]:
                build_ppc_tracks(imx_object, find)
            elif imx_object.tag == "StopConnection":
                build_stop_connections(imx_object, find)
            elif imx_object.tag == "TrackCircuit":
                build_track_circuit(imx_object, find)
            elif imx_object.tag == "AxleCounterSection":
                build_axle_counter_section(imx_object, find)

            elif imx_object.tag == "Workzone":
                second_process_list.append(imx_object)
            elif imx_object.tag == "TemporaryShuntingArea":
                second_process_list.append(imx_object)

            else:
                if imx_object.geometry is None:
                    logger.warning(f"{imx_object.tag} haz no geometry builder!")

    for imx_object in second_process_list:
        if imx_object.tag == "Workzone":
            build_work_zones(imx_object, find)
        elif imx_object.tag == "TemporaryShuntingArea":
            build_temporary_shunting_areas(imx_object, find)
