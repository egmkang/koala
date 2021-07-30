import asyncio

from koala.server import koala_host
from koala.network.constant import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.network.tcp_session import TcpSocketSession
from koala.logger import logger


_session_manager = SocketSessionManager()
codec_id = CODEC_ECHO


async def echo_handler(session: SocketSession, msg: object):
    if not session.is_client:
        await session.send_message(msg)
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


koala_host.init_server(globals())
koala_host.register_user_handler(str, echo_handler)
koala_host.listen(5555, codec_id)
koala_host.create_task(client())
koala_host.run_server()
