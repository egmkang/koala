import asyncio
from koala.singleton import Singleton
from koala.logger import logger
from koala.network.constant import WINDOW_SIZE
from koala.network.codec import Codec
from koala.network.codec_manager import CodecManager
from koala.network.tcp_session import TcpSocketSession
from koala.network import session_id_gen


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
        conn = TcpSocketSession(
            session_id_gen.new_session_id(), codec, reader, writer)
        await conn.recv_message()

    async def listen(self, port: int, codec_id: int):
        codec = _codec_manager.get_codec(codec_id)
        if codec is None:
            logger.error("listen port:%d failed, CodecID:%d not found" %
                         (port, codec_id))
            return

        async def callback(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
            assert codec
            await self._handle_new_session(codec, reader, writer)

        try:
            await asyncio.start_server(callback, port=port, limit=WINDOW_SIZE)
            logger.info("listen port:%d CodecID:%d success" % (port, codec_id))
        except Exception as e:
            logger.error("listen port:%d Exception:%s" % (port, e))

    def create_task(self, co):
        self._loop.create_task(co)

    def run(self):
        self._loop.run_forever()
