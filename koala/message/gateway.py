from typing import List, Optional
from pydantic import BaseModel
from koala.message.util import json_message


@json_message
class NotifyConnectionComing(BaseModel):
    service_type: str = ""
    actor_id: str = ""
    session_id: int = 0
    token: bytes = b""


@json_message
class NotifyConnectionAborted(BaseModel):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""


@json_message
class RequestCloseConnection(BaseModel):
    session_id: int = 0
    service_type: str = ""


@json_message
class NotifyNewMessage(BaseModel):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""
    message: bytes = b""


@json_message
class RequestSendMessageToPlayer(BaseModel):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
    message: bytes = b""


@json_message
class RequestChangeMessageDestination(BaseModel):
    session_id: int = 0
    new_service_type: str = ""
    new_actor_id: str = ""
