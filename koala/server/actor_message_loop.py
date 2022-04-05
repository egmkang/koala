import asyncio
import time
import traceback
import weakref
from koala.typing import *
from koala import utils
from koala.message import RpcResponse, RpcRequest
from koala.message.rpc_message import RpcMessage
from koala.server import rpc_meta
from koala.network.socket_session import SocketSession
from koala.server.actor_base import ActorBase
from koala.server.rpc_exception import RpcException, RPC_ERROR_UNKNOWN
from koala.logger import logger


_mailbox_loop_id = 1


def _new_loop_id():
    global _mailbox_loop_id
    _mailbox_loop_id += 1
    return _mailbox_loop_id


async def _send_error_resp(session: SocketSession, request_id: int, e: Exception):
    resp = RpcResponse()
    resp.request_id = request_id
    if isinstance(e, RpcException):
        resp.error_code = e.code
        resp.error_str = e.msg
    else:
        resp.error_code = RPC_ERROR_UNKNOWN
        resp.error_str = traceback.format_exc()
    await session.send_message(resp)


async def _dispatch_actor_rpc_request(
    actor: ActorBase, session: Optional[SocketSession], req: RpcRequest
):
    try:
        method = rpc_meta.get_rpc_impl_method((req.service_name, req.method_name))
        if method is None:
            raise RpcException.method_not_found()

        assert actor.context
        actor.context.last_message_time = time.time()

        result = method.__call__(actor, *req.args, **req.kwargs)
        if asyncio.iscoroutine(result):
            result = await result
        resp = RpcResponse()
        resp.request_id = req.request_id
        raw_response = utils.pickle_dumps(result)

        if session:
            await session.send_message(RpcMessage.from_msg(resp, raw_response))
    except Exception as e:
        logger.error(
            "_dispatch_actor_rpc_request, Actor:%s/%s, Exception:%s, StackTrace:%s"
            % (actor.type_name, actor.uid, e, traceback.format_exc())
        )
        if session:
            await _send_error_resp(session, req.request_id, e)


async def _dispatch_actor_message_in_loop(actor: ActorBase):
    loop_id = _new_loop_id()
    context = actor.context
    assert context

    if context.loop_id != 0:
        return
    context.loop_id = loop_id
    loaded = False

    try:
        try:
            await actor.activate_async()
            loaded = True
        except Exception as e:
            logger.error(
                "Actor:%s/%s ActivateAsync Fail, Exception:%s, StackTrace:%s"
                % (actor.type_name, actor.uid, e, traceback.format_exc())
            )
            context.loop_id = 0
            return
        while True:
            # 让出CPU给其他协程, 防止某些协程等待时间过长
            await asyncio.sleep(0)
            o = cast(
                Tuple[weakref.ReferenceType[SocketSession], object],
                await context.pop_message(),
            )
            if o is None:
                logger.info(
                    "Actor:%s/%s exit message loop" % (actor.type_name, actor.uid)
                )
                break
            session, msg = o[0]() if o[0] else None, o[1]
            if isinstance(msg, RpcRequest):
                context.reentrant_id = msg.reentrant_id
                await _dispatch_actor_rpc_request(actor, session, msg)
            else:
                await actor.dispatch_message(msg)
    except Exception as e:
        logger.error(
            "_dispatch_actor_message_loop, Exception:%s, StackTrace:%s"
            % (e, traceback.format_exc())
        )
        pass

    try:
        if loaded:
            await actor.deactivate_async()
    except Exception as e:
        logger.error(
            "Actor:%s/%s DeactivateAsync Fail, Exception:%s, StaceTrace:%s"
            % (actor.type_name, actor.uid, e, traceback.format_exc())
        )

    if context.loop_id == loop_id:
        context.reentrant_id = -1
        context.loop_id = 0
    logger.info("Actor:%s/%s loop:%d finished" % (actor.type_name, actor.uid, loop_id))


def run_actor_message_loop(actor: ActorBase):
    assert actor.context
    if actor.context.loop_id == 0:
        asyncio.create_task(_dispatch_actor_message_in_loop(actor))
    pass


async def dispatch_actor_message(actor: ActorBase, session: SocketSession, msg: object):
    assert actor.context
    if isinstance(msg, RpcRequest):
        req = cast(RpcRequest, msg)
        if actor.context.reentrant_id == req.reentrant_id:
            # 这边要直接派发
            asyncio.create_task(_dispatch_actor_rpc_request(actor, session, req))
            return
    weak_session = weakref.ref(session)
    await actor.context.push_message((weak_session, msg))
