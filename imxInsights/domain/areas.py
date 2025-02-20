from dataclasses import dataclass

from lxml.etree import _Element as Element
from shapely import Polygon

from imxInsights.utils.shapely.shapely_gml import GmlShapelyFactory


@dataclass
class Area:
    name: str
    coordinates: str
    shapely: Polygon

    @staticmethod
    def from_element(element: Element, name: str | None = None) -> "Area":
        coordinates_element = element.find(".//{http://www.opengis.net/gml}coordinates")
        if coordinates_element is None or coordinates_element.text is None:
            raise ValueError("Coordinates element or its text content is missing.")  # noqa: TRY003

        coordinates = coordinates_element.text
        tag_str = str(element.tag)  # Ensuring element.tag is a string
        name_value = tag_str.split("}")[1] if not name else name

        return Area(
            name=name_value,
            coordinates=coordinates,
            shapely=Polygon(GmlShapelyFactory.parse_coordinates(coordinates)),
        )


@dataclass
class ImxAreas:
    user_area: Area | None = None
    work_area: Area | None = None
    context_area: Area | None = None

    @staticmethod
    def from_element(element: Element) -> "ImxAreas":
        self = ImxAreas()

        user_area = element.find(".//{http://www.prorail.nl/IMSpoor}UserArea")
        if user_area is not None:
            self.user_area = Area.from_element(user_area)

        work_area = element.find(".//{http://www.prorail.nl/IMSpoor}WorkArea")
        if work_area is not None:
            self.work_area = Area.from_element(work_area)

        context_area = element.find(".//{http://www.prorail.nl/IMSpoor}ContextArea")
        if context_area is not None:
            self.context_area = Area.from_element(context_area)

        return self
