import asyncio
from koala.membership.server_node import ServerNode
from koala.server.actor_interface import ActorInterfaceType
from koala import utils
from koala.message.rpc_message import RpcMessage
from koala.server.rpc_meta import *
from koala.message import RpcRequest
from koala.server.rpc_exception import *
from koala.server.rpc_future import *
from koala.server.actor_context import ActorContext
from koala.server import rpc_request_id
from koala.placement.placement import Placement


DEFAULT_RPC_TIMEOUT = 5.0


async def _rpc_call(unique_id: int) -> object:
    future = asyncio.get_event_loop().create_future()
    add_future(unique_id, future)
    await asyncio.wait_for(future, timeout=DEFAULT_RPC_TIMEOUT)
    result = future.result()
    return result


PLACEMENT: Placement | None = None


class _RpcMethodObject(object):
    def __init__(
        self,
        actor_type: str,
        actor_id: ActorID,
        method_name: str,
        reentrant_id: int,
        server_node: Optional[ServerNode] = None,
        check_position: bool = True,
    ):
        self.actor_type = actor_type
        self.actor_id = actor_id
        self.method_name = method_name
        self.reentrant_id = reentrant_id
        self.server_node: Optional[ServerNode] = server_node
        self.check_position = check_position
        pass

    async def __send_request(self, *arg, **kwargs):
        # position
        global PLACEMENT
        if not PLACEMENT:
            PLACEMENT = Placement.instance()

        position = await PLACEMENT.find_position(self.actor_type, self.actor_id)
        if self.server_node:
            position = self.server_node
        if position is None:
            raise Exception("Placement Service Not Valid")

        session = position.session
        if session is None:
            raise Exception(
                "Target Server Not Valid, ServerUID: %d" % position.server_uid
            )

        req = RpcRequest()
        req.request_id = rpc_request_id.new_request_id()
        req.service_name = self.actor_type
        req.method_name = self.method_name
        # Actor底层支持str和int两种类型
        req.actor_id = self.actor_id
        req.reentrant_id = self.reentrant_id
        req.server_id = position.server_uid
        if not self.check_position:
            req.server_id = 0

        raw_args = utils.pickle_dumps((arg, kwargs))
        await session.send_message(RpcMessage.from_msg(req, raw_args))
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
                    Placement.instance().remove_position_cache(
                        self.actor_type, self.actor_id
                    )
                    continue
                raise e


class _RpcProxyObject(object):
    def __init__(
        self,
        i_type: Type,
        uid: ActorID,
        context: Optional[ActorContext],
        server_node: Optional[ServerNode] = None,
        check_position: bool = True,
    ):
        self.service_name = i_type.__qualname__
        self.uid = uid
        self.context = None
        if context is not None:
            self.context = weakref.ref(context)
        self.server_node = server_node
        self.check_position = check_position
        pass

    def __getattr__(self, name: str):
        ctx: Optional[ActorContext] = None
        if self.context is not None:
            ctx = self.context()
        if ctx is not None:
            reentrant_id = ctx.reentrant_id
        else:
            reentrant_id = rpc_request_id.new_reentrant_id()
        method = _RpcMethodObject(
            self.service_name,
            self.uid,
            name,
            reentrant_id,
            self.server_node,
            self.check_position,
        )
        return method


def get_rpc_proxy(
    i_type: Type[ActorInterfaceType],
    uid: ActorID,
    context: Optional[ActorContext] = None,
    server_node: Optional[ServerNode] = None,
    check_postion: bool = True,
) -> ActorInterfaceType:
    o = _RpcProxyObject(i_type, uid, context, server_node, check_postion)
    return cast(ActorInterfaceType, o)
