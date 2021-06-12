from typing import List, Optional
from koala.message.base import SimpleMessage
from dataclasses import dataclass


@dataclass
class NotifyConnectionComing(SimpleMessage):
    service_type: str = ""
    actor_id: str = ""
    session_id: int = 0
    token: bytes = b""


@dataclass
class NotifyConnectionAborted(SimpleMessage):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""


@dataclass
class RequestCloseConnection(SimpleMessage):
    session_id: int = 0
    service_type: str = ""


@dataclass
class NotifyNewMessage(SimpleMessage):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""
    message: bytes = b""


@dataclass
class RequestSendMessageToPlayer(SimpleMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
    message: bytes = b""


@dataclass
class RequestChangeMessageDestination(SimpleMessage):
    session_id: int = 0
    new_service_type: str = ""
    new_actor_id: str = ""
