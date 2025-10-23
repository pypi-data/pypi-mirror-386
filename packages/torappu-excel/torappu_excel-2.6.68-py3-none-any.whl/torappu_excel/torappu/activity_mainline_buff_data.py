from ..common import BaseStruct


class ActivityMainlineBuffData(BaseStruct):
    missionGroupList: dict[str, "ActivityMainlineBuffData.MissionGroupData"]
    periodDataList: list["ActivityMainlineBuffData.PeriodData"]
    apSupplyOutOfDateDict: dict[str, int]
    constData: "ActivityMainlineBuffData.ConstData"

    class MissionGroupData(BaseStruct):
        id: str
        bindBanner: str
        sortId: int
        zoneId: str
        missionIdList: list[str]

    class PeriodDataStepData(BaseStruct):
        isBlock: bool
        favorUpDesc: str | None
        unlockDesc: str | None
        bindStageId: str | None
        blockDesc: str | None

    class PeriodData(BaseStruct):
        id: str
        startTime: int
        endTime: int
        favorUpCharDesc: str
        favorUpImgName: str
        newChapterImgName: str
        newChapterZoneId: str | None
        stepDataList: list["ActivityMainlineBuffData.PeriodDataStepData"]

    class ConstData(BaseStruct):
        favorUpStageRange: str
