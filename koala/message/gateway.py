from typing import List, Optional
from koala.message.base import JsonMessage


class RequestAccountLogin(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    session_id: int = 0


class ResponseAccountLogin(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


class NotifyNewActorSession(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    actor_type: str = ""
    actor_id: str = ""
    session_id: int = 0


class NotifyActorSessionAborted(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


class RequestCloseSession(JsonMessage):
    session_id: int = 0
    actor_type: str = ""


class NotifyNewActorMessage(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


class RequestSendMessageToSession(JsonMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
