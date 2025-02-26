from collections import defaultdict
from collections.abc import Callable

from loguru import logger
from shapely import MultiLineString, MultiPoint, Point  # GeometryCollection

from imxInsights.domain.imxObject import ImxObject


def safe_find(
    find: Callable[[str], ImxObject | None], ref: str | None
) -> ImxObject | None:
    if ref is None:
        logger.warning("Received a None reference; skipping lookup.")
        return None
    obj = find(ref)
    if obj is None:
        logger.warning(f"Could not find object for reference: {ref}")
    return obj


def build_ppc_tracks(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    version = imx_object.imx_file.imx_version
    refs = []

    if version == "1.2.4":
        refs = [
            imx_object.properties.get("@beginDemarcatorRef"),
            imx_object.properties.get("@endDemarcatorRef"),
        ]
    elif version == "5.0.0":
        refs = [
            imx_object.properties.get("@demarcatorOneSideRef"),
            imx_object.properties.get("@demarcatorOtherSideRef"),
        ]
    elif version == "12.0.0":
        imx_object.geometry = MultiPoint(
            [
                ref.imx_object.geometry
                for ref in imx_object.refs
                if "DemarcationObject" in ref.field and ref.imx_object is not None
            ]
        )
        return
    else:
        logger.warning(f"{imx_object.tag} IMX {version} has no geometry builder!")
        return

    geometries = [
        obj.geometry
        for ref in refs
        if (obj := safe_find(find, ref)) is not None and isinstance(obj.geometry, Point)
    ]
    if geometries:
        if geometries:
            imx_object.geometry = MultiPoint(geometries)
        else:
            logger.warning(
                f"{imx_object.tag} has no valid Point geometries for MultiPoint."
            )

        imx_object.geometry = MultiPoint(geometries)


def build_stop_connections(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    version = imx_object.imx_file.imx_version
    ref = imx_object.properties.get("@signalRef")

    if version == "1.2.4":
        return  # Stop connection is an element of signal.
    elif version in ["5.0.0", "12.0.0"]:
        if (obj := safe_find(find, ref)) is not None:
            imx_object.geometry = obj.geometry
    else:
        logger.warning(f"{imx_object.tag} IMX {version} has no geometry builder!")


def build_generic_geometry(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None], property_key: str
) -> None:
    version = imx_object.imx_file.imx_version

    if version in ["1.2.4", "5.0.0"]:
        refs = imx_object.properties.get(property_key, "").split()
        geometries = [
            obj.geometry
            for ref in refs
            if (obj := safe_find(find, ref)) is not None
            and isinstance(obj.geometry, Point)
        ]
        if geometries:
            imx_object.geometry = MultiPoint(geometries)
    elif version == "12.0.0":
        imx_object.geometry = MultiPoint(
            [
                ref.imx_object.geometry
                for ref in imx_object.refs
                if "DemarcationObject" in ref.field and ref.imx_object is not None
            ]
        )
    else:
        logger.warning(f"{imx_object.tag} IMX {version} has no geometry builder!")


def build_track_circuit(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    build_generic_geometry(imx_object, find, "InsulatedJointRefs")


def build_axle_counter_section(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    build_generic_geometry(imx_object, find, "AxleCounterDetectionPointRefs")


def build_work_zones(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    version = imx_object.imx_file.imx_version

    if version in ["1.2.4", "5.0.0"]:
        refs = imx_object.properties.get("SectionRefs", "").split()
        multipoints = [
            obj.geometry
            for ref in refs
            if (obj := safe_find(find, ref)) is not None
            and isinstance(obj.geometry, Point)
        ]
        merged_multipoint = (
            MultiPoint(
                [
                    pt
                    for mp in multipoints
                    for pt in (mp.geoms if isinstance(mp, MultiPoint) else [mp])
                ]
            )
            if multipoints
            else None
        )
        if merged_multipoint is not None:
            imx_object.geometry = merged_multipoint

    elif version == "12.0.0":
        imx_object.geometry = MultiLineString(
            [item.geometry for item in imx_object.on_rail_geometry]
        )
    else:
        logger.warning(f"{imx_object.tag} IMX {version} has no geometry builder!")


def build_temporary_shunting_areas(
    imx_object: ImxObject, find: Callable[[str], ImxObject | None]
) -> None:
    version = imx_object.imx_file.imx_version

    if version in ["1.2.4", "5.0.0"]:
        refs = imx_object.properties.get("DemarcationRefs", "").split()
        points = [
            obj.geometry
            for ref in refs
            if (obj := safe_find(find, ref)) is not None
            and isinstance(obj.geometry, Point)
        ]
        if points:
            imx_object.geometry = MultiPoint(points)
    elif version == "12.0.0":
        logger.warning(f"{imx_object.tag} IMX {version} has no geometry builder!")


def add_specific_geometry(
    tree_dict: defaultdict[str, list[ImxObject]],
    find: Callable[[str], ImxObject | None],
) -> None:
    second_process_list = []
    for imx_objects in tree_dict.values():
        for imx_object in imx_objects:
            match imx_object.tag:
                case "PPCTrack" | "PpcTrack":
                    build_ppc_tracks(imx_object, find)
                case "StopConnection":
                    build_stop_connections(imx_object, find)
                case "TrackCircuit":
                    build_track_circuit(imx_object, find)
                case "AxleCounterSection":
                    build_axle_counter_section(imx_object, find)
                case "Workzone" | "TemporaryShuntingArea":
                    second_process_list.append(imx_object)
                case _ if imx_object.geometry is None:
                    logger.warning(f"{imx_object.tag} has no geometry builder!")

    for imx_object in second_process_list:
        match imx_object.tag:
            case "Workzone":
                build_work_zones(imx_object, find)
            case "TemporaryShuntingArea":
                build_temporary_shunting_areas(imx_object, find)
