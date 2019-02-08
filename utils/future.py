import weakref
from gevent.event import AsyncResult


_future_dict = weakref.WeakValueDictionary()


def add_future(unique_id, future: AsyncResult):
    _future_dict[unique_id] = future
    pass


def get_future(request_id) -> AsyncResult:
    future = _future_dict.pop(request_id, None)
    return future

