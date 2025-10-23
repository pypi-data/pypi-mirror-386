from msgspec import field

from ..common import BaseStruct


class RoguelikeGameZoneData(BaseStruct):
    id: str
    name: str
    clockPerformance: str | None
    displayTime: str | None
    description: str
    endingDescription: str
    backgroundId: str
    zoneIconId: str
    isHiddenZone: bool
    bgmSignal: str
    bgmSignalWithLowSan: str | None
    buffDescription: str | None = field(default=None)
