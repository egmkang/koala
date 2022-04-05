from koala.typing import *
from collections import abc


class ReadOnlyException(Exception):
    def __init__(self, *args, **kwargs):
        super(ReadOnlyException, self).__init__(*args, **kwargs)

    pass


def copy_readonly(o: object):
    if isinstance(o, ReadOnlyList):
        res = [copy_readonly(x) for x in o]
        return res
    elif isinstance(o, ReadOnlyDict):
        res = {}
        for k, v in o.items():
            res[k] = copy_readonly(v)
        return res
    return o


class ReadOnly:
    def copy(self):
        pass


class ReadOnlyDict(abc.Mapping, ReadOnly):
    def __getitem__(self, k):
        return self._data.__getitem__(k)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return self._data.__iter__()

    def __init__(self, data: abc.Mapping):
        super(ReadOnlyDict, self).__init__()
        self._data = dict()
        for k, v in data.items():
            if isinstance(v, list):
                self._data.__setitem__(k, ReadOnlyList(v))
            elif isinstance(v, dict):
                self._data.__setitem__(k, ReadOnlyDict(v))
            else:
                self._data.__setitem__(k, v)

    def __str__(self):
        return self._data.__str__()

    def __repr__(self):
        return self._data.__repr__()

    def __getattr__(self, item: str):
        raise AttributeError(f"ReadOnlyDict does not support {item}")

    def __setitem__(self, k, v):
        raise ReadOnlyException(f"ReadOnlyDict does not support set item")

    def copy(self):
        return copy_readonly(self)


class ReadOnlySet(abc.Set, ReadOnly):
    def __contains__(self, x: object) -> bool:
        return self._data.__contains__(x)

    def __len__(self) -> int:
        return len(self._data)

    def __iter__(self) -> Iterator:
        return self._data.__iter__()

    def __init__(self, s: set):
        super(ReadOnlySet, self).__init__()
        self._data = set()
        for k in s:
            self._data.add(k)

    def __str__(self):
        return self._data.__str__()

    def __repr__(self):
        return self._data.__repr__()

    def __eq__(self, other):
        if isinstance(other, ReadOnlySet):
            return self._data.__eq__(other._data)
        return self._data.__eq__(other)

    def __getattr__(self, item: str):
        raise AttributeError(f"ReadOnlySet does not support {item}")

    def copy(self):
        return copy_readonly(self)


class ReadOnlyList(abc.Sequence, ReadOnly):
    def __init__(self, data: abc.Sequence):
        super(ReadOnlyList, self).__init__()
        self._data = list()
        for item in data:
            if isinstance(item, list):
                self._data.append(ReadOnlyList(item))
            elif isinstance(item, dict):
                self._data.append(ReadOnlyDict(item))
            else:
                self._data.append(item)

    @overload
    def __getitem__(self, i: slice) -> abc.Sequence:
        ...

    @overload
    def __getitem__(self, i: int) -> Any:
        ...

    def __getitem__(self, i):
        return self._data[i]

    def __len__(self) -> int:
        return len(self._data)

    def __eq__(self, other):
        if isinstance(other, ReadOnlyList):
            return self._data.__eq__(other._data)
        return self._data.__eq__(other)

    def __str__(self):
        return self._data.__str__()

    def __repr__(self):
        return self._data.__repr__()

    def __setitem__(self, k, v):
        raise ReadOnlyException(f"ReadOnlyList does not support set item")

    def __getattr__(self, item: str):
        raise AttributeError(f"ReadOnlyList does not support {item}")

    def copy(self):
        return copy_readonly(self)


class ReadOnlyObject(object):
    def __setattr__(self, key, val):
        raise AttributeError(f"can not alter a const {self.__class__.__name__}")

    def __init__(self, data):
        super().__init__()
        for key, val in data.items():
            if isinstance(val, list):
                self.__dict__[key] = ReadOnlyList(val)
            elif isinstance(val, dict):
                self.__dict__[key] = ReadOnlyDict(val)
            else:
                self.__dict__[key] = val

    def __repr__(self):
        return self.__class__.__name__
