from pydantic import BaseModel
from koala.message.util import json_message


@json_message
class HeartBeatRequest(BaseModel):
    milli_seconds: int = 0


@json_message
class HeartBeatResponse(BaseModel):
    milli_seconds: int = 0


