from pydantic import BaseModel
from koala import default_dict
from koala.koala_typing import *


class JsonMessage(BaseModel):
    @classmethod
    def from_dict(cls, obj):
        return cls.model_validate(obj)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @property
    def pydantic_serializer(self):
        return self.__pydantic_serializer__


JsonVar = TypeVar("JsonVar", bound=JsonMessage)
__json_mapper: default_dict.DefaultDict[bytes, Any] = default_dict.DefaultDict()


def find_model(name: bytes) -> Optional[Type[JsonMessage]]:
    v = __json_mapper.get(name, None)
    if v:
        return v
    if __json_mapper.contains_key(name):
        return __json_mapper[name]
    return None


def register_model(cls):
    global __json_mapper
    __json_mapper[cls.__qualname__.encode()] = cls

    def decorator():
        return cls

    return decorator()
