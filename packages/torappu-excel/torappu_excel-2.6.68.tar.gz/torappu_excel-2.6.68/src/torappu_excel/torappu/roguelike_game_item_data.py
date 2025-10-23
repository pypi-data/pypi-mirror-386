from .roguelike_game_item_rarity import RoguelikeGameItemRarity
from .roguelike_game_item_sub_type import RoguelikeGameItemSubType
from .roguelike_game_item_type import RoguelikeGameItemType
from ..common import BaseStruct


class RoguelikeGameItemData(BaseStruct):
    id: str
    name: str
    description: str | None
    usage: str
    obtainApproach: str
    iconId: str
    itemIconGroupId: str | None
    type: RoguelikeGameItemType
    subType: RoguelikeGameItemSubType
    rarity: RoguelikeGameItemRarity
    sortId: int
    canSacrifice: bool
    tinyIconColor: str | None
    unlockCondDesc: str | None
    shortUsage: str | None
    value: int | None = None
