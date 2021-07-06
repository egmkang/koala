import asyncio
import time
from abc import abstractmethod
from koala.singleton import Singleton
from koala.logger import logger
from koala.typing import *
from koala.network.codec import Codec
from koala.network.constant import SOCKET_GC_INTERVAL


class SocketSession:
    @property
    @abstractmethod
    def session_id(self) -> int:
        pass

    @property
    @abstractmethod
    def create_time(self) -> int:
        pass

    @abstractmethod
    def heart_beat(self, time_now: float) -> None:
        pass

    @abstractmethod
    def is_dead(self, current_time) -> bool:
        pass

    @property
    @abstractmethod
    def is_closed(self) -> bool:
        pass

    @property
    @abstractmethod
    def is_client(self) -> bool:
        pass

    @property
    @abstractmethod
    def remote_address(self) -> str:
        pass

    @property
    @abstractmethod
    def codec(self) -> Codec:
        pass

    @abstractmethod
    async def send_message(self, msg: object) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass

    @abstractmethod
    def user_data(self) -> Optional[object]:
        pass

    @abstractmethod
    def set_user_data(self, data: object):
        pass


class SocketSessionManager(Singleton):
    def __init__(self):
        super(SocketSessionManager, self).__init__()
        self._session_dict: Dict[int, SocketSession] = dict()
        pass

    async def run(self):
        await self._gc_loop()

    async def _gc_loop(self):
        dead_list: List[SocketSession] = list()
        while True:
            logger.trace("gc_loop")
            current_time = time.time()
            for item in self._session_dict.values():
                if item.is_dead(current_time):
                    dead_list.append(item)
            for item in dead_list:
                self.remove_session(item.session_id)
                logger.warning("SocketSessionManager.gc_loop, SessionID:%d" % item.session_id)
            dead_list.clear()
            await asyncio.sleep(SOCKET_GC_INTERVAL)
        pass

    def add_session(self, session: SocketSession):
        session_id = session.session_id
        if session_id in self._session_dict:
            return
        self._session_dict[session_id] = session
        logger.info("SocketSessionManager.add_session, SessionID:%d, CodecID:%d" % (session_id, session.codec.codec_id))

    def remove_session(self, session_id: int):
        if session_id in self._session_dict:
            session = self._session_dict[session_id]
            if session:
                session.close()
            del self._session_dict[session_id]
            logger.info("SocketSessionManager.remove_session, SessionID:%d" % session_id)

    # 可选参数
    # 可以通过session id来获取SocketSession
    # 之后对SocketSession的引用, 建议搞成弱引用, 否则生命周期会被拉长
    def get_session(self, session_id: int) -> Optional[SocketSession]:
        if session_id in self._session_dict:
            return self._session_dict[session_id]
        return None
