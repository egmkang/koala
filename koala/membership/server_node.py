import time
from koala.typing import *
import weakref
from koala.network.socket_session import SocketSession


class ServerNodeMetaData(object):
    def __init__(self):
        self.server_uid = 0
        self.server_name = ""
        self.host = ""
        self.port = ""
        self.service_type: List[str] = []

    def _update(self, info):
        self.server_uid = info.server_uid
        self.server_name = info.server_name
        self.host = info.host
        self.port = info.port
        self.service_type = info.service_type
        pass


class ServerNode(ServerNodeMetaData):
    # 下面两个成员不是元数据
    # _proxy是一个弱引用, 减少一次查询
    _session_id: int
    _session: weakref.ReferenceType[SocketSession]

    def __init__(self, info: ServerNodeMetaData):
        super(ServerNode, self).__init__()
        super()._update(info)
        pass

    @property
    def session_id(self):
        return self._session_id

    @property
    def session(self) -> Optional[SocketSession]:
        if self._session is not None:
            return self._session()

    def set_session(self, session: SocketSession):
        self._session_id = session.session_id
        self._session = weakref.ref(session)
