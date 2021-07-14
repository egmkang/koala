import dataclasses
from koala.typing import *
from koala.utils import to_dict

JsonVar = TypeVar("JsonVar", bound='JsonMessage')
__json_mapper: Dict[str, Any] = dict()


def register_model(cls):
    global __json_mapper
    __json_mapper[cls.__qualname__] = cls


def find_model(name: str) -> Optional[Type['JsonMessage']]:
    if name in __json_mapper:
        return __json_mapper[name]
    return None


class JsonMeta(type):
    def __new__(mcs, class_name, class_parents, class_attr):
        cls = type.__new__(mcs, class_name, class_parents, class_attr)
        register_model(cls)
        return cls


@dataclasses.dataclass
class JsonMessage(metaclass=JsonMeta):
    @classmethod
    def from_dict(cls, kwargs: dict):
        return cls(**kwargs)

    def to_dict(self) -> dict:
        return cast(dict, to_dict(self))
