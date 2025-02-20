from dataclasses import dataclass, field
from typing import Optional

from lxml.etree import _Element
from shapely import LineString, Point, Polygon

from imxInsights.utils.shapely.shapely_gml import GmlShapelyFactory


@dataclass
class ImxGeographicLocation:
    """
    Represents a geographic location with attributes parsed from an XML element.

    Attributes:
        shapely: The Shapely geometric representation of the location.
        azimuth (Optional[float]): The azimuth of the location, if available.
        data_acquisition_method (Optional[str]): The method used to acquire the geographic data.
        accuracy (Optional[float]): The accuracy of the geographic data.
        srs_name (Optional[str]): The spatial reference system name.\

    """

    _element: _Element
    shapely: Point | LineString | Polygon = field(init=False)
    azimuth: float | None = field(init=False, default=None)
    data_acquisition_method: str | None = field(init=False, default=None)
    accuracy: float | None = field(init=False, default=None)
    srs_name: str | None = field(init=False, default=None)

    @staticmethod
    def from_element(element: _Element) -> Optional["ImxGeographicLocation"]:
        """
        Create an ImxGeographicLocation instance from an XML element.

        ??? info
            This method parses geographic location data from the given XML element
            and creates an instance of ImxGeographicLocation with the parsed data.

        Args:
            element (Element): The XML element to parse.

        Returns:
            Optional[ImxGeographicLocation]: An instance of ImxGeographicLocation if the element contains
            geographic location data, otherwise None.
        """

        location_node = element.find(
            ".//{http://www.prorail.nl/IMSpoor}GeographicLocation"
        )
        if element.tag == "{http://www.prorail.nl/IMSpoor}ObservedLocation":
            location_node = element  # pragma: no cover

        elif location_node is None:
            return None

        instance = ImxGeographicLocation(location_node)

        geometry = GmlShapelyFactory.shapely(location_node)
        if isinstance(geometry, Point | LineString | Polygon):
            instance.shapely = geometry
        else:
            raise TypeError(f"Unexpected geometry type: {type(geometry)}")

        instance.data_acquisition_method = location_node.attrib.get(
            "dataAcquisitionMethod", None
        )
        accuracy_value = location_node.attrib.get("accuracy", None)
        instance.accuracy = (
            float(accuracy_value) if accuracy_value is not None else None
        )

        azimuth_value = location_node.attrib.get("azimuth", None)
        instance.azimuth = float(azimuth_value) if azimuth_value is not None else None

        point_element = location_node.find(".//*[@srsName]")
        instance.srs_name = (
            point_element.attrib.get("srsName", None)
            if point_element is not None
            else None
        )

        return instance
