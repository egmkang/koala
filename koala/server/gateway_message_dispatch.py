import asyncio
from koala.logger import logger
from koala.json_util import json_loads
from koala.message import RpcMessage
from koala.message.gateway import *
from koala.placement.placement import get_placement_impl
from koala.server.actor_base import *
from koala.server.entity_manager import EntityManager
from koala.server.rpc_exception import RpcException
from koala.server.actor_message_loop import run_actor_message_loop, dispatch_actor_message

_entity_manager = EntityManager()


async def _dispatch_user_message_slow(session: SocketSession, actor_type: str, actor_id: str, msg: object):
    node = await get_placement_impl().find_position(actor_type, actor_id)
    if node is not None and node.server_uid == get_placement_impl().server_id():
        actor = _entity_manager.get_or_new_by_name(actor_type, actor_id)
        if actor is None:
            raise RpcException.entity_not_found()
        run_actor_message_loop(actor)
        await dispatch_actor_message(actor, session, msg)
    else:
        if node:
            node_session = node.session
            if node_session:
                await node_session.send_message(msg)
        else:
            logger.warning("Actor:%s/%s, cannot find position" % (actor_type, actor_id))
    pass


async def _dispatch_user_message(session: SocketSession, actor_type: str, actor_id: str, msg: object):
    # 这边获取到对象的位置, 然后直接把消息Push到对象Actor的MailBox里面
    # 如果没找到位置, 那么先去定位, 如果不在当前服务器内, 那么帮忙转发到一下
    node = get_placement_impl().find_position_in_cache(actor_type, actor_id)
    if node is not None and node.server_uid == get_placement_impl().server_id():
        actor = _entity_manager.get_or_new_by_name(actor_type, actor_id)
        if actor is None:
            raise RpcException.entity_not_found()
        run_actor_message_loop(actor)
        await dispatch_actor_message(actor, session, msg)
    else:
        asyncio.create_task(_dispatch_user_message_slow(session, actor_type, actor_id, msg))


async def process_gateway_account_login(session: SocketSession, msg: object):
    request = cast(RpcMessage, msg)
    req = cast(RequestAccountLogin, request.meta)
    body = request.body
    body_message: dict = json_loads(body)

    resp = ResponseAccountLogin()
    resp.session_id = req.session_id
    resp.actor_type = body_message.get("actor_type", "IPlayer")
    resp.actor_id = body_message.get("actor_id", "1")

    logger.warning("process_gateway_account_login, MUST REWRITE THIS FUNCTION, "
                   "SessionID:%s, OpenID:%s, ServerID:%s, Body:%s, DestActor:%s/%s" %
                   (req.session_id, req.open_id, req.server_id, body_message, resp.actor_type, resp.actor_id))
    await session.send_message(resp)


async def process_gateway_new_actor_session(session: SocketSession, msg: object):
    request = cast(RpcMessage, msg)
    notify = cast(NotifyNewActorSession, request.meta)
    await _dispatch_user_message(session, notify.actor_type, notify.actor_id, msg)


async def process_gateway_actor_session_aborted(session: SocketSession, msg: object):
    request = cast(RpcMessage, msg)
    notify = cast(NotifyActorSessionAborted, request.meta)
    await _dispatch_user_message(session, notify.actor_type, notify.actor_id, msg)


async def process_gateway_new_actor_message(session: SocketSession, msg: object):
    request = cast(RpcMessage, msg)
    notify = cast(NotifyNewActorMessage, request.meta)
    await _dispatch_user_message(session, notify.actor_type, notify.actor_id, msg)
