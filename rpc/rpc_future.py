import weakref
import asyncio
from .rpc_codec import RpcRequest


_future_dict = weakref.WeakValueDictionary()


def AddFuture(req: RpcRequest, future: asyncio.Future):
    _future_dict[req.request_id] = future
    pass

def GetFuture(request_id):
    future = _future_dict.pop(request_id, None)
    return future

def RemoveEmptyFuture():
    pass
