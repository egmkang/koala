import weakref
from .rpc_codec import RpcRequest
from gevent.event import AsyncResult


_future_dict = weakref.WeakValueDictionary()


def AddFuture(req: RpcRequest, future: AsyncResult):
    _future_dict[req.request_id] = future
    pass


def GetFuture(request_id) -> AsyncResult:
    future = _future_dict.pop(request_id, None)
    return future


def RemoveEmptyFuture():
    pass
