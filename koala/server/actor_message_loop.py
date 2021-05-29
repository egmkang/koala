import asyncio
import traceback
import weakref
from typing import cast
from koala.message.rpc import RpcResponse, RpcRequest
from koala.meta.rpc_meta import get_rpc_impl_method
from koala.network.socket_session import SocketSession
from koala.server.actor_base import ActorBase
from koala.server.rpc_exception import RpcException, RPC_ERROR_UNKNOWN
from koala.logger import logger


_mailbox_loop_id = 1


def _new_loop_id():
    global _mailbox_loop_id
    _mailbox_loop_id += 1
    return _mailbox_loop_id


async def _send_error_resp(proxy: SocketSession, request_id: int, e: Exception):
    resp = RpcResponse()
    resp.request_id = request_id
    if isinstance(e, RpcException):
        resp.error_code = e.code
        resp.error_str = e.msg
    else:
        resp.error_code = RPC_ERROR_UNKNOWN
        resp.error_str = traceback.format_exc()
    await proxy.send_message(resp)


async def _dispatch_actor_rpc_request(actor: ActorBase, proxy: SocketSession, req: RpcRequest):
    try:
        method = get_rpc_impl_method("%s.%s" % (req.service_name, req.method_name))
        if method is None:
            raise RpcException.method_not_found()

        result = method.__call__(actor, *req.args, **req.kwargs)
        resp = RpcResponse()
        resp.request_id = req.request_id
        resp.response = result

        if proxy:
            await proxy.send_message(resp)
    except Exception as e:
        logger.error("_dispatch_actor_rpc_request, Actor:%s/%s, Exception:%s, StackTrace:%s" %
                     (actor.type_name, actor.uid, e, traceback.format_exc()))
        await _send_error_resp(proxy, req.request_id, e)


async def _dispatch_actor_message_in_loop(actor: ActorBase):
    loop_id = _new_loop_id()
    context = actor.context
    if context.loop_id != 0:
        return
    context.loop_id = loop_id
    loaded = False

    try:
        try:
            await actor._activate_async()
            loaded = True
        except Exception as e:
            logger.error("Actor:%s/%s ActivateAsync Fail, Exception:%s, StackTrace:%s" %
                         (actor.type_name, actor.uid, e, traceback.format_exc()))
            context.loop_id = 0
            return
        while True:
            await asyncio.sleep(0)
            o = await context.pop_message()
            if o is None:
                logger.info("Actor:%s/%s exit message loop" % (actor.type_name, actor.uid))
                break
            proxy = o[0]()
            msg = o[1]
            if isinstance(msg, RpcRequest):
                context.reentrant_id = msg.reentrant_id
                await _dispatch_actor_rpc_request(actor, proxy, msg)
            else:
                await actor.dispatch_user_message(msg)
    except Exception as e:
        logger.error("_dispatch_actor_message_loop, Exception:%s, StackTrace:%s" %
                     (e, traceback.format_exc()))
        pass

    try:
        if loaded:
            await actor._deactivate_async()
    except Exception as e:
        logger.error("Actor:%s/%s DeactivateAsync Fail, Exception:%s, StaceTrace:%s" %
                     (actor.type_name, actor.uid, e, traceback.format_exc()))

    if context.loop_id == loop_id:
        context.reentrant_id = None
        context.loop_id = 0
    logger.info("Actor:%s/%s loop:%d finished" % (actor.type_name, actor.uid, loop_id))


def run_actor_message_loop(actor: ActorBase):
    if actor.context.loop_id == 0:
        asyncio.create_task(_dispatch_actor_message_in_loop(actor))
    pass


async def dispatch_actor_message(actor: ActorBase, proxy: SocketSession, msg: object):
    if isinstance(msg, RpcRequest):
        req = cast(RpcRequest, msg)
        if actor.context.reentrant_id == req.reentrant_id:
            # 这边要直接派发
            asyncio.create_task(_dispatch_actor_rpc_request(actor, proxy, req))
            return
    weak_proxy = weakref.ref(proxy)
    await actor.context.push_message((weak_proxy, msg))
