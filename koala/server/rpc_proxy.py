import asyncio
from asyncio.futures import Future
from koala.meta.rpc_meta import *
from koala.message.rpc import RpcRequest
from koala.server.rpc_exception import *
from koala.server.rpc_future import *
from koala.server.actor_context import ActorContext
from koala.server.rpc_request_id import new_request_id, new_reentrant_id
from koala.placement.placement import PlacementInjection


DEFAULT_RPC_TIMEOUT = 5.0
_placement = PlacementInjection()


async def _rpc_call(unique_id: int) -> object:
    future = asyncio.get_event_loop().create_future()
    add_future(unique_id, future)
    await asyncio.wait_for(future, timeout=DEFAULT_RPC_TIMEOUT)
    result = future.result()
    return result


class _RpcMethodObject(object):
    def __init__(self, service_type: str, actor_id: object, method_name: str, reentrant_id: int):
        self.service_name = service_type
        self.actor_id = actor_id
        self.method_name = method_name
        self.reentrant_id = reentrant_id
        pass

    async def __send_request(self, *arg, **kwargs):
        # position
        position = await _placement.impl.find_position(self.service_name, self.actor_id)
        if position is None:
            raise Exception("Placement Service Not Valid")

        proxy = position.session
        if proxy is None:
            raise Exception("Target Server Not Valid, ServerUID: %d" % position.server_uid)

        req = RpcRequest()
        req.request_id = new_request_id()
        req.service_name = self.service_name
        req.method_name = self.method_name
        req.actor_id = self.actor_id
        req.reentrant_id = self.reentrant_id
        req.args = arg
        req.kwargs = kwargs
        req.server_id = position.server_uid
        await proxy.send_message(req)
        return req.request_id

    async def __call__(self, *args, **kwargs):
        # 这边要检测一下位置是否发生变化
        # 如果位置发生变化, 可以补偿一次
        for x in range(2):
            try:
                request_id = await self.__send_request(*args, **kwargs)
                return await _rpc_call(request_id)
            except RpcException as e:
                if e.code == RPC_ERROR_POSITION_CHANGED:
                    _placement.impl.remove_position_cache(self.service_name, self.actor_id)
                    continue
                raise e


class _RpcProxyObject(object):
    def __init__(self, i_type: Type[T], uid: object, context: Optional[ActorContext]):
        self.service_name = i_type.__qualname__
        self.uid = uid
        self.context = None
        if context is not None:
            self.context = weakref.ref(context)
        pass

    def __getattr__(self, name: str):
        ctx: Optional[ActorContext] = None
        if self.context is not None:
            ctx = self.context()
        if ctx is not None:
            reentrant_id = ctx.reentrant_id
        else:
            reentrant_id = new_reentrant_id()
        method = _RpcMethodObject(self.service_name, self.uid, name, reentrant_id)
        return method


def get_rpc_proxy(i_type: Type[T], uid: object, context: ActorContext = None) -> T:
    o = _RpcProxyObject(i_type, uid, context)
    return cast(T, o)
