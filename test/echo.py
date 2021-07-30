import asyncio
import time

from koala.logger import logger
from koala.server import koala_host
from koala.network.constant import *
from koala.network.socket_session import SocketSession


finished = 0


async def echo_handler(session: SocketSession, msg: object):
    global finished
    finished += 1
    session.heart_beat(time.time())
    await session.send_message(msg)
    pass


async def qps():
    last = 0
    while True:
        await asyncio.sleep(1.0)
        v = finished
        if v - last > 0:
            logger.info("QPS:%d" % (v - last))
            last = v


koala_host.init_server(globals())
koala_host.register_user_handler(str, echo_handler)
koala_host.listen(5555, CODEC_ECHO)
koala_host.run_server()
