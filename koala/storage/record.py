from pydantic import BaseModel
from koala import utils


class Record(BaseModel):
    def to_dict(self) -> dict:
        return utils.to_dict(self)
