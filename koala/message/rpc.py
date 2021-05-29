from koala.typing import *


class RpcRequest:
    service_name: str
    method_name: str
    actor_id: ActorID
    reentrant_id: int
    request_id: int
    args: List[Any]
    kwargs: Dict[Any, Any]
    server_id: int


class RpcResponse:
    request_id: int
    error_code: int
    error_str: str
    response: Any


