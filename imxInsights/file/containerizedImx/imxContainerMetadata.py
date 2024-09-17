from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import dateparser
from lxml.etree import _Element as Element
from lxml.etree import _ElementTree as ElementTree

from imxInsights.domain.areas import Areas
from imxInsights.domain.imxEnums import (
    Imx12DataExchangePhaseEnum,
    Imx12ProjectDisciplineEnum,
)
from imxInsights.exceptions import exception_handler
from imxInsights.exceptions.imxExceptions import ImxDuplicatedPuicsInContainer


@dataclass
class ImxContainerMetadata:
    # todo: not sure if this is on petal or just over the zip container. if specific for core make explicit
    external_project_reference: str | None = None
    project_name: str | None = None
    project_discipline: Imx12ProjectDisciplineEnum | None = None
    data_exchange_phase: Imx12DataExchangePhaseEnum | None = None
    created_date: datetime | None = None
    planned_delivery_date: datetime | None = None
    areas: Areas | None = None

    @staticmethod
    def from_element(
        element: Element | ElementTree | None,
    ) -> Optional["ImxContainerMetadata"]:
        if element is None:
            return None

        self = ImxContainerMetadata()

        project_metadata_element = element.find(
            ".//{http://www.prorail.nl/IMSpoor}ProjectMetadata"
        )

        if project_metadata_element is not None:
            self.external_project_reference = project_metadata_element.get(
                "externalProjectReference", None
            )
            self.project_name = project_metadata_element.get("projectName", None)

            project_discipline = project_metadata_element.get("projectDiscipline", None)
            if project_discipline is not None:
                self.project_discipline = Imx12ProjectDisciplineEnum.from_string(
                    project_discipline
                )

            data_exchange_phase = project_metadata_element.get(
                "dataExchangePhase", None
            )
            if data_exchange_phase is not None:
                self.data_exchange_phase = Imx12DataExchangePhaseEnum.from_string(
                    data_exchange_phase
                )

            created_date_str = project_metadata_element.get("createdDate", None)
            self.created_date = (
                dateparser.parse(created_date_str) if created_date_str else None
            )

            planned_delivery_date_str = project_metadata_element.get(
                "plannedDeliveryDate", None
            )
            self.planned_delivery_date = (
                dateparser.parse(planned_delivery_date_str)
                if planned_delivery_date_str
                else None
            )

            return self

        else:
            exception = ImxDuplicatedPuicsInContainer("ProjectMetadata not present")
            exception_handler.handle_exception(exception)
            return None
