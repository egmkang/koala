from .entity import Entity


ENTITY_TYPE_PLAYER = 1


class Player(Entity):
    def __init__(self, uid: int):
        super().__init__(ENTITY_TYPE_PLAYER, uid)

