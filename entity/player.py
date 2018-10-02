from .entity_type import *
from .entity import *

class Player(Entity):
    def __init__(self, uid:int):
        super().__init__(ENTITY_TYPE_PLAYER, uid)

