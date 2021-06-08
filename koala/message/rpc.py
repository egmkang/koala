from koala.typing import *
from pydantic import BaseModel
from koala.message.util import json_message


@json_message
class RpcRequest(BaseModel):
    service_name: str
    method_name: str
    actor_id: ActorID
    reentrant_id: int
    request_id: int
    server_id: int


@json_message
class RpcResponse(BaseModel):
    request_id: int
    error_code: int
    error_str: str

