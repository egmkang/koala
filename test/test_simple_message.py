from koala.message import *
from dataclasses import dataclass
from koala.message.base import SimpleMessage


@dataclass
class B(SimpleMessage):
    service_name: str = ""
    method_name: str = ""
    actor_id: str = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0
    _args: Optional[list] = None
    _kwargs: Optional[dict] = None


class TestSimpleMessage:
    def test_simple_message(self):
        b = B(server_id=1, service_name="s1212", method_name="func", reentrant_id=2222, request_id=3)
        d = b.to_dict()
        b1 = B.from_dict(d)
        assert b.server_id == b1.server_id
        assert b == b1

