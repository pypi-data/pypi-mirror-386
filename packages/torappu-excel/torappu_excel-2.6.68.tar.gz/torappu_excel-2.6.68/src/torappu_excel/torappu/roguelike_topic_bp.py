from .item_type import ItemType
from ..common import BaseStruct


class RoguelikeTopicBP(BaseStruct):
    id: str
    level: int
    tokenNum: int
    nextTokenNum: int
    itemID: str
    itemType: ItemType
    itemCount: int
    isGoodPrize: bool
    isGrandPrize: bool
