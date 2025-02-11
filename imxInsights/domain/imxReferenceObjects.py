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
    imx_object: Any | None = None
    status: RefStatus = RefStatus.NOT_PRESENT

    def __post_init__(self):
        if self.imx_object:
            self.status = RefStatus.PRESENT

    @property
    def display(self) -> str:
        return f"{self.field} {self.lookup} {f'{self.status.value} ({self.imx_object.tag})' if self.imx_object else self.status.value}"
