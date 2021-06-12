from koala.typing import *
from koala.message.base import SimpleMessage
from dataclasses import dataclass


@dataclass
class RpcRequest(SimpleMessage):
    service_name: str = ""
    method_name: str = ""
    actor_id: ActorID = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0
    _args: Optional[list] = None
    _kwargs: Optional[dict] = None

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs


@dataclass
class RpcResponse(SimpleMessage):
    request_id: int = 0
    error_code: int = 0
    error_str: str = ""
    _response: Optional[object] = None

    @property
    def response(self):
        return self._response
