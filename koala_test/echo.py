import asyncio
import time

from koala.logger import logger
from koala.server import server_base
from koala.network.constant import *
from koala.network.socket_session import SocketSession


finished = 0


async def echo_handler(proxy: SocketSession, msg: object):
    global finished
    finished += 1
    proxy.heart_beat(time.time())
    await proxy.send_message(msg)
    pass


async def qps():
    last = 0
    while True:
        await asyncio.sleep(1.0)
        v = finished
        if v - last > 0:
            logger.info("QPS:%d" % (v - last))
            last = v


server_base.init_server()
server_base.register_user_handler(str, echo_handler)
server_base.listen(5555, CODEC_ECHO)


server_base.run_server()
