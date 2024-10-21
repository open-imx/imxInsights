from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from lxml.etree import _Element as Element
from lxml.etree import _ElementTree as ElementTree

from imxInsights.domain.areas import ImxAreas
from imxInsights.utils.xml_helpers import parse_date


@dataclass
class SingleImxMetadata:
    project_puic: str | None = None
    project_name: str | None = None
    project_type: str | None = None
    external_project_reference: str | None = None
    created_date: datetime | None = None
    planned_delivery_date: datetime | None = None
    areas: ImxAreas | None = None

    @staticmethod
    def from_element(
        element: Element | ElementTree | None,
    ) -> Optional["SingleImxMetadata"]:
        if element is None:
            return None

        self = SingleImxMetadata()

        project_element = element.find(".//{http://www.prorail.nl/IMSpoor}Project")
        if project_element is None:
            return None

        # get props
        self.project_puic = project_element.get("puic")
        self.project_name = project_element.get("name")

        project_metadata_element = element.find(
            ".//{http://www.prorail.nl/IMSpoor}ProjectMetadata"
        )
        if project_metadata_element is None:
            return None

        self.external_project_reference = project_metadata_element.get(
            "externalProjectReference"
        )
        self.created_date = parse_date(project_metadata_element.get("createdDate"))
        self.planned_delivery_date = parse_date(
            project_metadata_element.get("plannedDeliveryDate")
        )
        self.project_type = project_metadata_element.get("projectType")

        if isinstance(element, ElementTree):
            self.areas = ImxAreas.from_element(element.getroot())
        else:
            self.areas = ImxAreas.from_element(element)

        return self
