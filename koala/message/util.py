from koala.typing import *
from pydantic import BaseModel


JsonVar = TypeVar("JsonVar", bound=BaseModel)
__json_mapper: Dict[str, Type[BaseModel]] = dict()


def json_message(cls: Type[JsonVar]) -> Type[JsonVar]:
    global __json_mapper
    __json_mapper[cls.__qualname__] = cls
    return cls


def find_model(name: str) -> Optional[Type[BaseModel]]:
    if name in __json_mapper:
        return __json_mapper[name]
    return None
