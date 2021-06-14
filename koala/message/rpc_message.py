import dataclasses
from koala.typing import *
from koala.message.base import JsonMessage


@dataclasses.dataclass
class RpcMessage:
    meta: JsonMessage
    body: Optional[bytes] = None

    @classmethod
    def from_msg(cls, meta: JsonMessage, body: Optional[bytes] = None) -> 'RpcMessage':
        msg = RpcMessage(meta=meta, body=body)
        return msg
