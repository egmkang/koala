import typing


_KT = typing.TypeVar("_KT")
_VT = typing.TypeVar("_VT")


class DefaultDict(typing.DefaultDict[_KT, _VT], typing.Generic[_KT, _VT]):
    def contains_key(self, key: _KT) -> bool:
        if key in self:
            return True
        return False
