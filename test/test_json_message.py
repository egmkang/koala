from koala.message import *
from dataclasses import dataclass
from koala.message.base import JsonMessage


@dataclass(slots=True)
class B(JsonMessage):
    service_name: str = ""
    method_name: str = ""
    actor_id: str = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0
    _args: Optional[list] = None
    _kwargs: Optional[dict] = None


@dataclass(slots=True)
class A(JsonMessage):
    b: B
    a: str


class TestJsonMessage:
    def test_simple_message(self):
        b = B(
            server_id=1,
            service_name="s1212",
            method_name="func",
            reentrant_id=2222,
            request_id=3,
        )
        d = b.to_dict()
        b1 = B.from_dict(d)
        assert b.server_id == b1.server_id
        assert b == b1

    def test_escape_private_field(self):
        b = B(
            server_id=1,
            service_name="s1212",
            method_name="func",
            reentrant_id=2222,
            request_id=3,
        )
        b._args = [1111]
        a = A(b=b, a="222")
        # 只需要判断两层就行了
        d = a.to_dict()
        for k, v in d.items():
            if k.startswith("_"):
                assert False
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    if k1.startswith("_"):
                        assert False
        assert True
