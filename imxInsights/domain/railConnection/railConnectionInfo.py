from dataclasses import dataclass


@dataclass
class RailConnectionInfo:
    pass


@dataclass
class RailConnectionInfos:
    rail_con_infos: list[RailConnectionInfo]
