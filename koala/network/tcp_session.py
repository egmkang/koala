import asyncio
import time
import traceback

from koala.message import RpcMessage
from koala.typing import *
from koala.network.buffer import Buffer
from koala.logger import logger
from koala.network.codec import Codec
from koala.network.codec_manager import CodecManager
from koala.network.socket_session import SocketSession
from koala.network import session_id_gen
from koala.network.constant import SOCKET_HEART_BEAT, WINDOW_SIZE
from koala.network import event_handler

_codec_manager: CodecManager = CodecManager()


class TcpSocketSession(SocketSession):
    def __init__(
        self,
        session_id: int,
        codec: Codec,
        reader: asyncio.StreamReader,
        writer: asyncio.StreamWriter,
    ):
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

        event_handler._process_income_socket(self)

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
        return self._stop or (
            current_time - self._last_update_time >= SOCKET_HEART_BEAT
        )

    @property
    def is_closed(self) -> bool:
        return self._stop

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
        logger.info(
            "TcpSession.close, SessionID:%d Address:%s"
            % (self.session_id, self._address)
        )
        self._stop = True
        try:
            self._writer.close()
        except:
            pass

    @classmethod
    def get_real_type(cls, o: object):
        if isinstance(o, RpcMessage):
            return o.meta.__class__
        return o.__class__

    async def recv_message(self):
        try:
            while not self._stop:
                msg = await self._recv_data()
                if msg is None:
                    break
                await event_handler._process_socket_message(
                    self, self.get_real_type(msg), msg
                )
        except Exception as e:
            logger.error(
                "TcpSocketSession.recv_message, SessionID:%d Exception:%s, StackTrace:%s"
                % (self.session_id, e, traceback.format_exc())
            )
            self.close()
        finally:
            event_handler._process_close_socket(session_id=self.session_id)

    async def _recv_data(self):
        while not self._stop:
            msg = self._codec.decode(self._buffer)
            if msg is not None:
                return msg
            self._buffer.shrink()

            data = await self._reader.read(1024)
            if not data or len(data) == 0:
                logger.error(
                    "TcpSocketSession.recv, SessionID:%d recv 0" % self.session_id
                )
                return None
            self._buffer.append(data)

    async def send_message(self, msg: object):
        try:
            data = self._codec.encode(msg)
            self._writer.write(data)
        except Exception as e:
            logger.error(
                "send_message, Exception:%s, StackTrace:%s"
                % (e, traceback.format_exc())
            )
        # await self._writer.drain()

    @classmethod
    async def connect(
        cls, host: str, port: int, codec_id: int
    ) -> Optional[SocketSession]:
        codec = _codec_manager.get_codec(codec_id)
        if not codec:
            logger.error(
                "connect %s:%d failed, CodecID:%d not found" % (host, port, codec_id)
            )
            return None

        reader, writer = await asyncio.open_connection(
            host=host, port=port, limit=WINDOW_SIZE
        )
        session = TcpSocketSession(
            session_id_gen.new_session_id(), codec, reader, writer
        )
        session._is_client = True
        asyncio.create_task(session.recv_message())
        return session
