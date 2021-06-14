from typing import List, Optional
from koala.message.base import JsonMessage
from dataclasses import dataclass


@dataclass
class NotifyConnectionComing(JsonMessage):
    service_type: str = ""
    actor_id: str = ""
    session_id: int = 0
    token: bytes = b""


@dataclass
class NotifyConnectionAborted(JsonMessage):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""


@dataclass
class RequestCloseConnection(JsonMessage):
    session_id: int = 0
    service_type: str = ""


@dataclass
class NotifyNewMessage(JsonMessage):
    session_id: int = 0
    service_type: str = ""
    actor_id: str = ""
    message: bytes = b""


@dataclass
class RequestSendMessageToPlayer(JsonMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
    message: bytes = b""


@dataclass
class RequestChangeMessageDestination(JsonMessage):
    session_id: int = 0
    new_service_type: str = ""
    new_actor_id: str = ""
