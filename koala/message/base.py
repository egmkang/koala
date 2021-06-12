from koala.typing import *


JsonVar = TypeVar("JsonVar", bound='SimpleMessage')
__json_mapper: Dict[str, Any] = dict()


def register_model(cls):
    global __json_mapper
    __json_mapper[cls.__qualname__] = cls


def find_model(name: str) -> Optional[Type['SimpleMessage']]:
    if name in __json_mapper:
        return __json_mapper[name]
    return None


class JsonMeta(type):
    def __new__(mcs, class_name, class_parents, class_attr):
        cls = type.__new__(mcs, class_name, class_parents, class_attr)
        register_model(cls)
        return cls


class SimpleMessage(metaclass=JsonMeta):
    @classmethod
    def from_dict(cls, kwargs: dict):
        return cls(**kwargs)

    def to_dict(self) -> dict:
        d = {}
        for k, v in self.__dict__.items():
            if k[0] == '_':
                continue
            d[k] = v
        return d
