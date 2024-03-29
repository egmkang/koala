from typing import List, Optional
from koala.message.base import JsonMessage
from dataclasses import dataclass


@dataclass(slots=True)
class RequestAccountLogin(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    session_id: int = 0


@dataclass(slots=True)
class ResponseAccountLogin(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass(slots=True)
class NotifyNewActorSession(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    actor_type: str = ""
    actor_id: str = ""
    session_id: int = 0


@dataclass(slots=True)
class NotifyActorSessionAborted(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass(slots=True)
class RequestCloseSession(JsonMessage):
    session_id: int = 0
    actor_type: str = ""


@dataclass(slots=True)
class NotifyNewActorMessage(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass(slots=True)
class RequestSendMessageToSession(JsonMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
