import weakref
from pydantic import BaseModel, PrivateAttr
from koala.typing import *
from koala.network.socket_session import SocketSession


class ServerNode(BaseModel):
    server_uid: int = 0
    server_name: str = ""
    host: str = ""
    port: str = ""
    desc: str = ""
    service_type: Dict[str, str] = {}
    # 下面两个成员不是元数据
    # _session是一个弱引用, 减少一次查询
    _session: Optional[weakref.ReferenceType[SocketSession]] = PrivateAttr(default=None)
    _session_id: int = PrivateAttr(default=0)

    @property
    def session_id(self):
        return self._session_id

    @property
    def session(self) -> Optional[SocketSession]:
        if self._session is not None:
            return self._session()
        return None

    def set_session(self, session: SocketSession):
        self._session_id = session.session_id
        self._session = weakref.ref(session)


if __name__ == "__main__":
    s = ServerNode()
    print(s, s.session, s.session_id)
