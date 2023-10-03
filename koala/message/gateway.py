from typing import List, Optional
from koala.message.base import JsonMessage, register_model


@register_model
class RequestAccountLogin(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    session_id: int = 0


@register_model
class ResponseAccountLogin(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@register_model
class NotifyNewActorSession(JsonMessage):
    open_id: str = ""
    server_id: int = 0
    actor_type: str = ""
    actor_id: str = ""
    session_id: int = 0


@register_model
class NotifyActorSessionAborted(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@register_model
class RequestCloseSession(JsonMessage):
    session_id: int = 0
    actor_type: str = ""


@register_model
class NotifyNewActorMessage(JsonMessage):
    session_id: int = 0
    actor_type: str = ""
    actor_id: str = ""


@register_model
class RequestSendMessageToSession(JsonMessage):
    session_ids: Optional[List[int]] = None
    session_id: int = 0
