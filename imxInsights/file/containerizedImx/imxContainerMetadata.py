from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from lxml.etree import _Element as Element
from lxml.etree import _ElementTree as ElementTree

from imxInsights.domain.areas import ImxAreas
from imxInsights.domain.imxEnums import (
    Imx12DataExchangePhaseEnum,
    Imx12ProjectDisciplineEnum,
)
from imxInsights.utils.xml_helpers import parse_date


@dataclass
class ImxContainerMetadata:
    # todo: not sure if this is on petal or just over the zip container. if specific for core make explicit
    external_project_reference: str | None = None
    project_name: str | None = None
    project_discipline: Imx12ProjectDisciplineEnum | None = None
    data_exchange_phase: Imx12DataExchangePhaseEnum | None = None
    created_date: datetime | None = None
    planned_delivery_date: datetime | None = None
    areas: ImxAreas | None = None

    @staticmethod
    def from_element(
        element: Element | ElementTree | None,
    ) -> Optional["ImxContainerMetadata"]:
        """
        Creates an ImxContainerMetadata instance from an XML element.

        Args:
            element (Optional[Union[Element, ElementTree]]): The XML element containing project metadata.

        Returns:
            Optional[ImxContainerMetadata]: An instance of ImxContainerMetadata or None if the element is None.
        """
        if element is None:
            return None

        self = ImxContainerMetadata()
        project_metadata_element = element.find(
            ".//{http://www.prorail.nl/IMSpoor}ProjectMetadata"
        )

        if project_metadata_element is None:
            return None

        self.external_project_reference = project_metadata_element.get(
            "externalProjectReference"
        )
        self.project_name = project_metadata_element.get("projectName")

        project_discipline = project_metadata_element.get("projectDiscipline")
        if project_discipline:
            self.project_discipline = Imx12ProjectDisciplineEnum.from_string(
                project_discipline
            )

        data_exchange_phase = project_metadata_element.get("dataExchangePhase")
        if data_exchange_phase:
            self.data_exchange_phase = Imx12DataExchangePhaseEnum.from_string(
                data_exchange_phase
            )

        self.created_date = parse_date(
            project_metadata_element.get("createdDate", None)
        )
        self.planned_delivery_date = parse_date(
            project_metadata_element.get("plannedDeliveryDate", None)
        )

        if isinstance(element, ElementTree):
            self.areas = ImxAreas.from_element(element.getroot())
        else:
            self.areas = ImxAreas.from_element(element)

        return self
