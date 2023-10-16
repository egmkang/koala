from pydantic import BaseModel
from koala import default_dict
from koala.koala_typing import *
from pydantic._internal._model_construction import ModelMetaclass


_json_mapper: default_dict.DefaultDict[bytes, type] = default_dict.DefaultDict()


class JsonMetaClass(ModelMetaclass):
    def __new__(
        mcs,
        *args,
        **kwargs,
    ) -> type:
        _type = super().__new__(
            mcs,
            *args,
            **kwargs,
        )
        global _json_mapper
        _json_mapper[_type.__qualname__.encode()] = _type

        return _type


class JsonMessage(BaseModel, metaclass=JsonMetaClass):
    @classmethod
    def from_dict(cls, obj):
        return cls.model_validate(obj)

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump()

    @property
    def pydantic_serializer(self):
        return self.__pydantic_serializer__


def find_model(name: bytes) -> Optional[Type[JsonMessage]]:
    v = _json_mapper.get(name, None)
    if v:
        return v
    if _json_mapper.contains_key(name):
        return _json_mapper[name]
    return None
