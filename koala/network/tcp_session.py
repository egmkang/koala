import asyncio
import time
from koala.typing import *
from koala.network.buffer import Buffer
from koala.logger import logger
from koala.network.codec import Codec
from koala.network.codec_manager import CodecManager
from koala.network.socket_session import SocketSession
from koala.network.session_id_gen import new_session_id
from koala.network.constant import SOCKET_PROXY_HEART_BEAT, WINDOW_SIZE
from koala.network.event_handler import _process_socket_message, _process_income_socket, _process_close_socket


_codec_manager: CodecManager = CodecManager()


class TcpSocketSession(SocketSession):
    def __init__(self, session_id: int,
                 codec: Codec,
                 reader: asyncio.StreamReader,
                 writer: asyncio.StreamWriter):
        super(TcpSocketSession, self).__init__()
        self._session_id = session_id
        self._create_time = int(time.time())
        self._last_update_time = time.time()
        self._codec = codec
        self._is_client = False
        self._reader = reader
        self._writer = writer
        self._address = "%s:%s" % writer.get_extra_info("peername")
        self._buffer = Buffer()
        self._user_data: Optional[object] = None
        self._stop = False

        _process_income_socket(self)

    def __del__(self):
        pass

    @property
    def session_id(self) -> int:
        return self._session_id

    @property
    def create_time(self) -> int:
        return self._create_time

    def heart_beat(self, time_now: float) -> None:
        self._last_update_time = time_now

    def is_dead(self, current_time: float) -> bool:
        return current_time - self._last_update_time >= SOCKET_PROXY_HEART_BEAT

    @property
    def is_client(self) -> bool:
        return self._is_client

    @property
    def remote_address(self) -> str:
        return self._address

    @property
    def codec(self) -> Codec:
        return self._codec

    def user_data(self) -> Optional[object]:
        return self._user_data

    def set_user_data(self, data: object):
        self._user_data = data

    def close(self):
        logger.info("close rpc connection %s" % self._address)
        self._writer.close()
        self._stop = True

    async def recv_message(self):
        try:
            while not self._stop:
                msg = await self._recv_data()
                if msg is None:
                    break
                await _process_socket_message(self, msg)
        except Exception as e:
            logger.error("TcpSocketSession.recv_message, SessionID:%d Exception:%s" % (self.session_id, e))
            pass
        finally:
            _process_close_socket(session_id=self.session_id)

    async def _recv_data(self):
        while not self._stop:
            msg = self._codec.decode(self._buffer)
            if msg is not None:
                return msg
            self._buffer.shrink()

            data = await self._reader.read(1024)
            if not data or len(data) == 0:
                logger.error("TcpSocketSession.recv, SessionID:%d recv 0" % self.session_id)
                return None
            self._buffer.append(data)

    async def send_message(self, msg: object):
        data = self._codec.encode(msg)
        self._writer.write(data)
        await self._writer.drain()

    @classmethod
    async def connect(cls, host: str, port: int, codec_id: int) -> Optional[SocketSession]:
        codec = _codec_manager.get_codec(codec_id)
        if not codec:
            logger.error("connect %s:%d failed, CodecID:%d not found" % (host, port, codec_id))
            return None

        reader, writer = await asyncio.open_connection(host=host, port=port, limit=WINDOW_SIZE)
        session = TcpSocketSession(new_session_id(), codec, reader, writer)
        session._is_client = True
        _process_income_socket(session)
        asyncio.create_task(session.recv_message())
        return session

