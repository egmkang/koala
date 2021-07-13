import dataclasses
from koala.typing import *
from koala.message.base import JsonMessage


@dataclasses.dataclass
class RpcMessage:
    meta: JsonMessage
    body: bytes = b""

    @classmethod
    def from_msg(cls, meta: JsonMessage, body: bytes = b"") -> 'RpcMessage':
        msg = RpcMessage(meta=meta, body=body)
        return msg
