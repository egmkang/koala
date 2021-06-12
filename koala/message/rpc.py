from koala.typing import *
from pydantic import BaseModel, PrivateAttr
from koala.message.util import json_message


@json_message
class RpcRequest(BaseModel):
    service_name: str = ""
    method_name: str = ""
    actor_id: ActorID = ""
    reentrant_id: int = 0
    request_id: int = 0
    server_id: int = 0
    _args: Optional[list] = PrivateAttr(default=None)
    _kwargs: Optional[dict] = PrivateAttr(default=None)

    class Config:
        validate_assignment = False

    @property
    def args(self):
        return self._args

    @property
    def kwargs(self):
        return self._kwargs


@json_message
class RpcResponse(BaseModel):
    request_id: int = 0
    error_code: int = 0
    error_str: str = ""
    _response: Optional[object] = PrivateAttr(default=None)

    class Config:
        validate_assignment = False

    @property
    def response(self):
        return self._response

