import asyncio

from koala.server import server_base
from koala.network.constant import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.network.tcp_session import TcpSocketSession
from koala.logger import logger


_proxy_manager = SocketSessionManager()
codec_id = CODEC_RPC


async def echo_handler(proxy: SocketSession, msg: object):
    if not proxy.is_client:
        await proxy.send_message(msg)
        logger.info("recv msg: %s" % msg)
    else:
        logger.info("client recv msg: %s" % msg)
    pass


async def client():
    await asyncio.sleep(2.0)
    session = await TcpSocketSession.connect("127.0.0.1", 5555, codec_id)
    count = 0
    while True:
        await asyncio.sleep(1.0)
        if session is not None:
            await session.send_message("hello world: %d" % count)
            logger.info("%d" % count)
            count += 1
    pass


server_base.init_server()
server_base.register_user_handler(str, echo_handler)
server_base.listen(5555, codec_id)

server_base.create_task(client())
server_base.run_server()
