import weakref
from asyncio.futures import Future


__future_dict: weakref.WeakValueDictionary[int, Future] = weakref.WeakValueDictionary()


def add_future(unique_id: int, future: Future):
    __future_dict[unique_id] = future
    pass


def get_future(request_id: int) -> Future | None:
    future = __future_dict.pop(request_id, None)
    return future
