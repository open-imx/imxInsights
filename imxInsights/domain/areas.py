from dataclasses import dataclass

from lxml.etree import _Element as Element
from shapely.geometry import Polygon

from imxInsights.utils.shapley_helpers import GmlShapleyFactory


@dataclass
class Areas:
    name: str
    coordinates: str
    shapely: Polygon

    @staticmethod
    def from_element(element: Element) -> "Areas":
        coordinates_element = element.find(".//{http://www.opengis.net/gml}coordinates")
        if coordinates_element is None or coordinates_element.text is None:
            raise ValueError("Coordinates element or its text content is missing.")  # noqa: TRY003

        coordinates = coordinates_element.text
        return Areas(
            name=element.tag,
            coordinates=coordinates,
            shapely=GmlShapleyFactory.gml_polygon_to_shapely(coordinates),
        )
