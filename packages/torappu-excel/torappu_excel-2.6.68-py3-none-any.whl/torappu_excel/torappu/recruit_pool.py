from msgspec import field

from .based_recruit_pool import RecruitConstants
from ..common import BaseStruct


class RecruitPool(BaseStruct):
    recruitTimeTable: list["RecruitPool.RecruitTime"]
    recruitConstants: "RecruitConstants"
    recruitCharacterList: None = field(default=None)
    maskTypeWeightTable: None = field(default=None)

    class RecruitTime(BaseStruct):
        timeLength: int
        recruitPrice: int
        accumRate: float | None = field(default=None)
