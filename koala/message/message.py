from koala.typing import *
from koala.message.base import JsonMessage
from dataclasses import dataclass


@dataclass
class RpcRequest(JsonMessage):
    service_name: str = ""
    method_name: str = ""
    actor_id: ActorID = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0
    _args: Optional[list] = None        # 这两个参数, 在RpcMessage的Body里面携带着
    _kwargs: Optional[dict] = None

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs


@dataclass
class RpcResponse(JsonMessage):
    request_id: int = 0
    error_code: int = 0
    error_str: str = ""
    _response: Optional[object] = None      # 这个参数在RpcMessage的Body内

    @property
    def response(self):
        return self._response


@dataclass
class RequestHeartBeat(JsonMessage):
    milli_seconds: int = 0


@dataclass
class ResponseHeartBeat(JsonMessage):
    milli_seconds: int = 0
