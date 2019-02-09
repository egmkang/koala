import gevent
from gevent.monkey import patch_all
patch_all()

import sys
sys.path.append("..")

from sample.player import TestPlayer
from sample.entity_type import ENTITY_TYPE_PLAYER
from rpc.rpc_proxy import RpcProxyObject
from rpc.rpc_server import RpcServer
from rpc.rpc_method import rpc_method
from entity.entity import ActorContext
from entity.entity_manager import *
from utils.log import logger


manager: EntityManager = get_entity_manager(ENTITY_TYPE_PLAYER)


@rpc_method()
def say_hello_to_player(uid: int, name: str):
    player = manager.get_entity(uid)
    if player is not None:
         return player.say(name)
    return None


def test_task():
    gevent.sleep(18)
    proxy = RpcProxyObject(TestPlayer, ENTITY_TYPE_PLAYER, 123, ActorContext.empty())
    response = proxy.say('lilith')
    logger.info("proxy.say('lilith') => %s" % (response))


if __name__ == "__main__":
    server = RpcServer(1001)

    server.listen_port(18888)

    gevent.spawn(lambda: test_task())
    server.run()
