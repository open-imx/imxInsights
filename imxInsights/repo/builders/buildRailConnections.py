from collections.abc import Callable

from shapely.geometry import LineString, MultiLineString, Point
from shapely.ops import linemerge

from imxInsights.domain.imxObject import ImxObject
from imxInsights.exceptions.imxExceptions import ImxRailConnectionRefNotPresent
from imxInsights.repo.builders.buildExceptions import BuildExceptions
from imxInsights.utils.shapely.shapley_helpers import reverse_line


def build_rail_connections(
    get_by_types: Callable[[list[str]], list[ImxObject]],
    find: Callable[[str], ImxObject | None],
    exceptions: BuildExceptions,
):
    """
    Constructs rail connections by merging geometries of referenced track and passage objects.

    ??? info
        This function retrieves rail connection objects, fetches their referenced track and passage objects,
        merges their geometries, and assigns the resulting geometry to the rail connection. It handles exceptions
        when references are missing or invalid and logs these exceptions.

    Args:
        get_by_types : A callable to retrieve objects by their types.
        find: A callable to find an object by its unique identifier.
        exceptions: An object to collect exceptions that occur during the build process.
    """

    rail_connections = get_by_types(["RailConnection"])
    for rail_connection in rail_connections:
        track_ref = rail_connection.element.attrib.get("trackRef")
        passage_refs_str = rail_connection.element.attrib.get("passageRefs", "")

        passage_refs = passage_refs_str.split() if passage_refs_str else []

        if not passage_refs:
            passage_refs_elements = rail_connection.element.findall(".//{*}PassageRefs")
            if passage_refs_elements:
                passage_ref_text = passage_refs_elements[0].text
                if passage_ref_text:
                    passage_refs = (
                        passage_ref_text.split()
                        if " " in passage_ref_text
                        else [passage_ref_text]
                    )

        geometries = []
        for passage_ref in passage_refs:
            passage_obj = find(passage_ref)
            if passage_obj is None:
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"Passage {passage_ref} of rail_connection {rail_connection.puic} not present"
                    ),
                    rail_connection.puic,
                )
            else:
                geographic_location = passage_obj.geographic_location
                if geographic_location:
                    geometries.append(geographic_location.shapely)

        if track_ref:
            track_obj = find(track_ref)
            if track_obj is None:
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"Track {track_ref} of rail_connection {rail_connection.puic} not present"
                    ),
                    rail_connection.puic,
                )
            else:
                geographic_location = track_obj.geographic_location
                if geographic_location:
                    geometries.append(geographic_location.shapely)

        if geometries:
            # Ensure geometries are of the expected type for linemerge
            valid_geometries = [
                geom
                for geom in geometries
                if isinstance(geom, LineString | MultiLineString)
            ]
            line_geometry = linemerge(valid_geometries)

            # Check if linemerge resulted in a LineString
            if isinstance(line_geometry, MultiLineString):
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"RailConnection {rail_connection.puic} merge geometries result in MultiLineString"
                    ),
                    rail_connection.puic,
                )
                continue

            if not isinstance(line_geometry, LineString):
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"RailConnection {rail_connection.puic} merge geometries result is not a LineString"
                    ),
                    rail_connection.puic,
                )
                continue

            from_node_ref = rail_connection.extension_properties.get(
                "extension.MicroLink.FromMicroNode.@nodeRef"
            )
            from_junction = find(from_node_ref) if from_node_ref else None
            if from_junction is None or from_junction.geographic_location is None:
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"RailConnection {rail_connection.puic} missing or invalid FromMicroNode"
                    ),
                    rail_connection.puic,
                )
                continue

            to_node_ref = rail_connection.extension_properties.get(
                "extension.MicroLink.ToMicroNode.@nodeRef"
            )
            to_junction = find(to_node_ref) if to_node_ref else None
            if to_junction is None or to_junction.geographic_location is None:
                exceptions.add(
                    ImxRailConnectionRefNotPresent(
                        msg=f"RailConnection {rail_connection.puic} missing or invalid ToMicroNode"
                    ),
                    rail_connection.puic,
                )
                continue

            first_coord_distance_from_from_node = Point(
                line_geometry.coords[0]
            ).distance(from_junction.geographic_location.shapely)
            first_coord_distance_from_to_node = Point(line_geometry.coords[0]).distance(
                to_junction.geographic_location.shapely
            )

            if first_coord_distance_from_to_node < first_coord_distance_from_from_node:
                line_geometry = reverse_line(line_geometry)

            rail_connection.geometry = line_geometry
