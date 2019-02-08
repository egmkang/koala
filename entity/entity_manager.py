from utils.log import logger
from .entity import Entity
from .entity_factory import new_entity

_global_entity_manager = dict()


class EntityManager:
    def __init__(self, entity_type: int):
        self._entity_type = entity_type
        self._entities = dict()

    def get_entity(self, uid):
        if uid not in self._entities:
            return None
        return self._entities[uid]

    def get_or_new_entity(self, uid):
        player = self.get_entity(uid)
        if player is None:
            player = new_entity(self._entity_type, uid)
            self._add_entity(player)
        return player

    def _add_entity(self, entity: Entity):
        uid = entity.get_uid()
        if uid in self._entities:
            logger.error("EntityManager.add_entity, Entity:(%s, %s) is not None" % (self._entity_type, uid))
        self._entities[uid] = entity

    def remove_entity(self, uid):
        del self._entities[uid]

    def count(self):
        return len(self._entities)

    def map(self, fn):
        for k, v in self._entities:
            fn(k, v)


def get_entity_manager(entity_type: int):
    global _global_entity_manager
    if entity_type not in _global_entity_manager:
        _global_entity_manager[entity_type] = EntityManager(entity_type)
    return _global_entity_manager[entity_type]

