from rpc.rpc_server import *
from rpc.rpc_method import rpc_method
from .entity_type import ENTITY_TYPE_PLAYER
from entity.entity_factory import entity_factory
import gevent


class TestPlayer(Entity):
    def __init__(self, uid: int):
        super().__init__(ENTITY_TYPE_PLAYER, uid)
        pass

    def on_active(self):
        gevent.sleep(0)
        pass

    def on_deactive(self):
        pass

    @rpc_method(ENTITY_TYPE_PLAYER)
    def say(self, name):
        logger.info("LogicPlayer:%d, call say(%s)" % (self.get_uid(), name))
        return "my name is %s, your is %s" % (self.get_uid(), name)


@entity_factory(ENTITY_TYPE_PLAYER)
def player_factory(uid: int):
    player = TestPlayer(uid)
    return player

