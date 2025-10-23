from .player_act_fun3 import PlayerActFun3
from .player_act_fun4 import PlayerActFun4
from .player_act_fun5 import PlayerActFun5
from .player_act_fun6 import PlayerActFun6
from ..common import BaseStruct


class PlayerAprilFool(BaseStruct):
    act3fun: PlayerActFun3
    act4fun: PlayerActFun4
    act5fun: PlayerActFun5
    act6fun: PlayerActFun6
