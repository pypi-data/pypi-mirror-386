from .roguelike_buff import RoguelikeBuff
from .roguelike_game_char_buff_type import RoguelikeGameCharBuffType
from ..common import BaseStruct


class RoguelikeGameCharBuffData(BaseStruct):
    id: str
    buffType: RoguelikeGameCharBuffType
    iconId: str
    outerName: str
    innerName: str
    functionDesc: str
    desc: str
    buffs: list[RoguelikeBuff]
