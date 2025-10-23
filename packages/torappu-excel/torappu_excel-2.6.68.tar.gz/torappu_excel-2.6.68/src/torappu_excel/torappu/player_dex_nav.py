from .player_character_hand_book import PlayerCharacterHandBook
from .player_enemy_hand_book import PlayerEnemyHandBook
from .player_formula_unlock_record import PlayerFormulaUnlockRecord
from ..common import BaseStruct


class PlayerDexNav(BaseStruct):
    character: dict[str, PlayerCharacterHandBook]
    enemy: PlayerEnemyHandBook
    formula: PlayerFormulaUnlockRecord
    teamV2: dict[str, dict[str, int]]
