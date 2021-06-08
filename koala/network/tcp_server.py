import asyncio
from koala.singleton import Singleton
from koala.logger import logger
from koala.network.constant import WINDOW_SIZE
from koala.network.codec import Codec
from koala.network.codec_manager import CodecManager
from koala.network.tcp_session import TcpSocketSession
from koala.network.session_id_gen import *


_codec_manager = CodecManager()


class TcpServer(Singleton):
    def __init__(self):
        super(TcpServer, self).__init__()
        self._loop = asyncio.get_event_loop()
        pass

    @classmethod
    async def _handle_new_session(cls, codec: Codec,
                                  reader: asyncio.StreamReader,
                                  writer: asyncio.StreamWriter):
        conn = TcpSocketSession(new_session_id(), codec, reader, writer)
        await conn.recv_message()

    def listen(self, port: int, codec_id: int):
        codec = _codec_manager.get_codec(codec_id)
        if codec is None:
            logger.error("listen port:%d failed, CodecID:%d not found" % (port, codec_id))
            return

        async def callback(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            assert codec
            await self._handle_new_session(codec, reader, writer)
        co = asyncio.start_server(callback, port=port, limit=WINDOW_SIZE, loop=self._loop)
        self.create_task(co)

    def create_task(self, co):
        self._loop.create_task(co)

    def run(self):
        self._loop.run_forever()
