import dataclasses
import inspect
from koala import default_dict
from koala.koala_typing import *
from koala.utils import to_dict

JsonVar = TypeVar("JsonVar", bound="JsonMessage")
__json_mapper: default_dict.DefaultDict[str, Any] = default_dict.DefaultDict()


def register_model(cls):
    global __json_mapper
    __json_mapper[cls.__qualname__] = cls


def find_model(name: str) -> Optional[Type["JsonMessage"]]:
    if __json_mapper.contains_key(name):
        return __json_mapper[name]
    return None


class JsonMeta(type):
    def __new__(cls, class_name, class_parents, class_attr):
        cls = type.__new__(cls, class_name, class_parents, class_attr)
        register_model(cls)
        return cls


@dataclasses.dataclass
class JsonMessage(metaclass=JsonMeta):
    @classmethod
    def from_dict(cls, kwargs: dict):
        parameters = inspect.signature(cls).parameters
        return cls(**{k: v for k, v in kwargs.items() if k in parameters})

    def to_dict(self) -> dict:
        return cast(dict, to_dict(self))
