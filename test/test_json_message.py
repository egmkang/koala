from koala.message import *
from koala.message.base import JsonMessage


class B2(JsonMessage):
    service_name: str = ""
    method_name: str = ""
    actor_id: str = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0

    def __init__(self, **data: Any) -> None:
        super().__init__(**data)
        self._args: Optional[list] = None
        self._kwargs: Optional[dict] = None
        pass


class A2(JsonMessage):
    b: B2
    a: str


class TestJsonMessage:
    def test_simple_message_v2(self):
        b = B2(
            server_id=1,
            service_name="s1212",
            method_name="func",
            reentrant_id=2222,
            request_id=3,
        )
        d = b.to_dict()
        b1 = B2.from_dict(d)
        assert b.server_id == b1.server_id
        assert b == b1

    def test_escape_private_field_v2(self):
        b = B2(
            server_id=1,
            service_name="s1212",
            method_name="func",
            reentrant_id=2222,
            request_id=3,
        )
        b._args = [1111]
        a = A2(b=b, a="222")
        # 只需要判断两层就行了
        d = a.to_dict()
        for k, v in d.items():
            if k.startswith("_"):
                assert False
            if isinstance(v, dict):
                for k1, v1 in v.items():
                    if k1.startswith("_"):
                        assert False

        s = a.__pydantic_serializer__.to_json(a)
        assert s
        assert type(s) == bytes
        assert True

    def test_find_model(self):
        v = find_model(b"1")
        assert not v
        b1 = find_model(b"B2")
        assert b1
        assert b1.__pydantic_serializer__
