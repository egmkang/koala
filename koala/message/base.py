from pydantic import BaseModel
from koala import default_dict
from koala.koala_typing import *
from pydantic._internal._model_construction import ModelMetaclass
from pydantic._internal._generics import PydanticGenericMetadata


JsonVar = TypeVar("JsonVar", bound="JsonMessage")
_json_mapper: default_dict.DefaultDict[bytes, Any] = default_dict.DefaultDict()


class JsonMeta(ModelMetaclass):
    def __new__(
        mcs,
        cls_name: str,
        bases: tuple[type[Any], ...],
        namespace: dict[str, Any],
        __pydantic_generic_metadata__: PydanticGenericMetadata | None = None,
        __pydantic_reset_parent_namespace__: bool = True,
        **kwargs: Any,
    ) -> type:
        _type = super().__new__(
            mcs,
            cls_name,
            bases,
            namespace,
            __pydantic_generic_metadata__,
            __pydantic_reset_parent_namespace__,
            **kwargs,
        )
        global _json_mapper
        _json_mapper[_type.__qualname__.encode()] = _type

        return _type


class JsonMessage(BaseModel, metaclass=JsonMeta):
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


if __name__ == "__main__":

    class TestJsonMessage(JsonMessage):
        value: int = 0
        name: str = ""

    a = TestJsonMessage(value=1, name="1212")
    print(1, a.to_dict())

    model = find_model(b"TestJsonMessage")
    print(2, model)

    if model:
        print(3, model.model_validate(a.to_dict()))

    print(4, _json_mapper)
