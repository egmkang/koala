from koala.message.base import SimpleMessage
from dataclasses import dataclass


@dataclass
class HeartBeatRequest(SimpleMessage):
    milli_seconds: int = 0


@dataclass
class HeartBeatResponse(SimpleMessage):
    milli_seconds: int = 0
