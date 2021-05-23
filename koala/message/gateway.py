from typing import List, Optional


class NotifyConnectionComing(object):
    def __init__(self):
        self.service_type = ""
        self.actor_id = ""
        self.session_id = 0
        self.token = b""


class NotifyConnectionAborted(object):
    def __init__(self):
        self.session_id = 0
        self.service_type = ""
        self.actor_id = ""


class RequestCloseConnection(object):
    def __init__(self):
        self.session_id = 0
        self.service_type = ""


class NotifyNewMessage(object):
    def __init__(self):
        self.session_id = 0
        self.service_type = ""
        self.actor_id = ""
        self.message = b""


class RequestSendMessageToPlayer(object):
    def __init__(self):
        self.session_ids: Optional[List[int]] = None
        self.session_id: int = 0
        self.message = b""


class RequestChangeMessageDestination(object):
    def __init__(self):
        self.session_id = 0
        self.new_service_type = ""
        self.new_actor_id = ""

