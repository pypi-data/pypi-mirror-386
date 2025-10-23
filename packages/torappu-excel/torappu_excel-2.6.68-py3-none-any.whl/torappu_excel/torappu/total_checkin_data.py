from .open_server_item_data import OpenServerItemData
from ..common import BaseStruct


class TotalCheckinData(BaseStruct):
    order: int
    item: OpenServerItemData
    colorId: int
