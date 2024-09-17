from dataclasses import dataclass
from typing import Any


@dataclass
class ImxRailConnection:
    track: Any
    passages: list[Any]
