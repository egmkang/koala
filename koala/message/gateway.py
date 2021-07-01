from typing import List, Optional
from koala.message.base import JsonMessage
from dataclasses import dataclass


@dataclass
class RequestAccountLogin(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    session_id: int = 0


@dataclass
class ResponseAccountLogin(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass
class NotifyNewActorSession(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    actor_type: str = ""
    actor_id: str = ""
    session_id: int = 0


@dataclass
class NotifyActorSessionAborted(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass
class RequestCloseSession(JsonMessage):
    session_id: int = 0
    actor_type: str = ""


@dataclass
class NotifyNewActorMessage(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@dataclass
class RequestSendMessageToSession(JsonMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
