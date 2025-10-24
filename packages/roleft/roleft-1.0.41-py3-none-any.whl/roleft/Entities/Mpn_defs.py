from abc import ABC
from dataclasses import dataclass
from xdatetime_defs import xdatetime


@dataclass
class MpnBase(ABC):
    Id: int
    CreateTime: xdatetime
