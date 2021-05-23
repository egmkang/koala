import time
import weakref
from typing import List, Dict
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
    def __init__(self, info: ServerNodeMetaData):
        super(ServerNode, self).__init__()
        super()._update(info)
        # 下面两个成员不是元数据
        # _proxy是一个弱引用, 减少一次查询
        self._session_id = 0
        self._proxy = None
        pass

    @property
    def session_id(self):
        return self._session_id

    @property
    def proxy(self) -> SocketSession:
        if self._proxy is not None:
            return self._proxy()

    def set_proxy(self, proxy: SocketSession):
        self._session_id = proxy.session_id
        self._proxy = weakref.ref(proxy)



