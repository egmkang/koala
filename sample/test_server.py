import sys
sys.path.append("..")

import gevent
from gevent.monkey import patch_all
patch_all()

from sample.player import TestPlayer, player_manager
from rpc.rpc_proxy import RpcProxyObject
from entity.entity import RpcContext
from rpc.rpc_server import rpc_method, RpcServer
from rpc.rpc_constant import RPC_ENTITY_TYPE_PLAYER
from utils.log import logger

@rpc_method
def say_hello_to_player(uid: int, name: str):
    player = player_manager.get_player(uid)
    if player is not None:
         return player.say(name)
    return None

def test_task():
    gevent.sleep(18)
    proxy = RpcProxyObject(TestPlayer, RPC_ENTITY_TYPE_PLAYER, 123, RpcContext.GetEmpty())
    response = proxy.say('lilith')
    logger.info("proxy.say('lilith') => %s" % (response))


if __name__ == "__main__":
    server = RpcServer(1001)

    server.listen_port(18888)

    gevent.spawn(lambda: test_task())
    server.run()
