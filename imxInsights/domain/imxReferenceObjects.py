from dataclasses import dataclass
from enum import Enum
from typing import Any


class RefStatus(Enum):
    PRESENT = "Present"
    NOT_PRESENT = "Not Present"


@dataclass
class ImxRef:
    field: str
    field_value: str
    lookup: str
    imx_object: Any | None = (
        None  # todo: make protocol for imx object.... so we can type hint instead of any
    )
    status: RefStatus = RefStatus.NOT_PRESENT

    def __post_init__(self):
        if self.imx_object:
            self.status = RefStatus.PRESENT

    @property
    def display(self) -> str:
        if self.imx_object:
            return f"{self.lookup}|{self.imx_object.tag if self.imx_object else ''}|{self.imx_object.name if self.imx_object else ''}"
        return f"{self.lookup}-{self.status.value}"
