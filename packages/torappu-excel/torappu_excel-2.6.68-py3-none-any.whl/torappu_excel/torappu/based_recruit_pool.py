from msgspec import field

from ..common import BaseStruct


class BasedRecruitPool(BaseStruct):
    recruitConstants: "BasedRecruitPool.RecruitConstants"

    class RecruitConstants(BaseStruct):
        tagPriceList: dict[str, int]
        maxRecruitTime: int
        rarityWeights: None = field(default=None)
        recruitTimeFactorList: None = field(default=None)


class RecruitConstants(BaseStruct):
    tagPriceList: dict[str, int]
    maxRecruitTime: int
    rarityWeights: None = field(default=None)
    recruitTimeFactorList: None = field(default=None)
