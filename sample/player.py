from rpc.rpc_server import *
from entity.player_manager import *
import gevent

player_manager = PlayerManager()


class TestPlayer(Player):
    def __init__(self, uid:int):
        super().__init__(uid)
        pass

    def on_active(self):
        gevent.sleep(0)
        pass

    def on_deactive(self):
        pass

    @player_rpc_method
    def say(self, name):
        logger.info("LogicPlayer:%d, call say(%s)" % (self.get_uid(), name))
        return "my name is %s, your is %s" % (self.get_uid(), name)


def player_factory(uid: int):
    player = TestPlayer(uid)
    return player


player_manager.player_factory = player_factory
