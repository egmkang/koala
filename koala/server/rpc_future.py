import weakref
from gevent.event import AsyncResult

__future_dict = weakref.WeakValueDictionary()


def add_future(unique_id: int, future: AsyncResult):
    __future_dict[unique_id] = future
    pass


def get_future(request_id: int) -> AsyncResult:
    future = __future_dict.pop(request_id, None)
    return future

