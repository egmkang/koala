from pydantic import BaseModel
from koala import utils
from koala.koala_typing import cast


class Record(BaseModel):
    def to_dict(self) -> dict:
        return cast(dict, utils.to_dict(self))
