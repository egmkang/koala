from sample.player import *


@rpc_method
def say_hello_to_player(uid: int, name: str):
    player = player_manager.get_player(uid)
    if player is not None:
         return player.say(name)
    return None

async def test_task():
    await asyncio.sleep(18)
    proxy = RpcProxyObject(TestPlayer, ENTITY_TYPE_PLAYER, 123, RpcContext.GetEmpty())
    response = await proxy.say('lilith')
    logger.info("await proxy.say('lilith') => %s" % (response))


server = RpcServer(1001)

server.listen(18888)

server.create_task(test_task())
server.run()
