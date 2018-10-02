from rpc.rpc_server import *
from entity.player import *
from entity.player_manager import *
from rpc.rpc_proxy import RpcProxyObject
import asyncio

player_manager = PlayerManager()

class TestPlayer(Player):
    def __init__(self, uid:int):
        super().__init__(uid)
        pass

    async def load_from_db(self):
        await asyncio.sleep(0)
        pass

    @player_rpc_method
    def say(self, name):
        logger.info("LogicPlayer:%d, call say(%s)" % (self.get_uid(), name))
        return "my name is %s, your is %s" % (self.get_uid(), name)


def PlayerFactory(uid: int):
    player = TestPlayer(uid)
    return player

player_manager.player_factory = PlayerFactory