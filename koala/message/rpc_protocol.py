import dataclasses
from koala.typing import *
from koala.message.base import SimpleMessage


@dataclasses.dataclass
class RpcProtocol:
    meta: SimpleMessage
    body: Optional[bytes] = None

    @classmethod
    def from_msg(cls, meta: SimpleMessage, body: Optional[bytes] = None) -> 'RpcProtocol':
        msg = RpcProtocol(meta=meta, body=body)
        msg.__class__ = meta.__class__
        return msg
