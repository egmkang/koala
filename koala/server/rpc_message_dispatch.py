import asyncio
import time
import traceback
from koala import utils
from koala.logger import logger
from koala.message import RpcRequest, RpcResponse, RequestHeartBeat, ResponseHeartBeat
from koala.message.rpc_message import RpcMessage
from koala.network.socket_session import SocketSession
from koala.server.rpc_future import *
from koala.server import actor_message_loop
from koala.server.actor_manager import ActorManager
from koala.server.rpc_exception import RpcException
from koala.placement.placement import Placement
from koala.koala_typing import *


_entity_manager = ActorManager()
_last_process_time = time.time()
_placement_instance: Placement | None = None


async def update_process_time():
    global _last_process_time
    while True:
        await asyncio.sleep(1.0)
        _last_process_time = time.time()


async def process_rpc_request_slow(session: SocketSession, request: object):
    global _placement_instance
    if not _placement_instance:
        _placement_instance = Placement.instance()

    placement = _placement_instance
    req, _ = cast(Tuple[RpcRequest, bytes], request)
    placement.remove_position_cache(req.service_name, req.actor_id)
    try:
        node = await placement.find_position(req.service_name, req.actor_id)
        if node is not None and node.server_uid == placement.server_id():
            actor = _entity_manager.get_or_new_by_name(req.service_name, req.actor_id)
            if actor is None:
                raise RpcException.entity_not_found()
            actor_message_loop.run_actor_message_loop(actor)
            await actor_message_loop.dispatch_actor_message(actor, session, req)
        else:
            await actor_message_loop._send_error_resp(
                session, req.request_id, RpcException.position_changed()
            )
    except Exception as e:
        logger.error(
            "process_rpc_request, Exception:%s, StackTrace:%s"
            % (e, traceback.format_exc())
        )
        await actor_message_loop._send_error_resp(session, req.request_id, e)
    pass


async def process_rpc_request(session: SocketSession, request: object):
    global _placement_instance
    if not _placement_instance:
        _placement_instance = Placement.instance()

    request = cast(RpcMessage, request)
    req, raw_args = request.meta, request.body if request.body else b""
    req = cast(RpcRequest, req)
    req._args, req._kwargs = utils.pickle_loads(raw_args)
    try:
        current_server_id = _placement_instance.server_id()
        node = Placement.instance().find_position_in_cache(
            req.service_name, req.actor_id
        )
        # server_id是0, 就可以忽略掉服务器ID检查, 可以做一些特殊的任务
        ignore_check_position = not req.server_id
        position_is_equal = (
            node is not None and node.server_uid == req.server_id == current_server_id
        )
        # rpc请求方, 和自己的pd缓存一定要是一致的
        # 否则就清掉自己的缓存, 然后重新查找一下定位
        if position_is_equal or ignore_check_position:
            actor = _entity_manager.get_or_new_by_name(req.service_name, req.actor_id)
            if actor is None:
                raise RpcException.entity_not_found()
            actor_message_loop.run_actor_message_loop(actor)
            await actor_message_loop.dispatch_actor_message(actor, session, req)
        else:
            asyncio.create_task(process_rpc_request_slow(session, request))
    except Exception as e:
        logger.error(
            "process_rpc_request, Exception:%s, StackTrace:%s"
            % (e, traceback.format_exc())
        )
        await actor_message_loop._send_error_resp(session, req.request_id, e)
    pass


async def process_rpc_response(session: SocketSession, response: object):
    response = cast(RpcMessage, response)
    resp, raw_response = response.meta, response.body if response.body else b""
    resp = cast(RpcResponse, resp)
    resp._response = utils.pickle_loads(raw_response)

    future = get_future(resp.request_id)
    if not future:
        logger.warning(
            "process_rpc_response, future not found, request_id:%d, remote_address:%s, result:%s"
            % (resp.request_id, session.remote_address, (resp.error_str, resp.response))
        )
        return
    if resp.error_code != 0:
        future.set_exception(Exception(resp.error_str))
    else:
        if resp:
            future.set_result(resp.response)
        else:
            future.set_result(None)


async def process_heartbeat_request(session: SocketSession, request: object):
    request = cast(RpcMessage, request)
    req = cast(RequestHeartBeat, request.meta)
    resp = ResponseHeartBeat()
    resp.milli_seconds = req.milli_seconds
    session.heart_beat(_last_process_time)
    await session.send_message(resp)
    logger.trace("process_rpc_heartbeat_request, SessionID:%d" % session.session_id)


async def process_heartbeat_response(session: SocketSession, response: object):
    now = int(time.time() * 1000)
    response = cast(RpcMessage, response)
    resp = cast(ResponseHeartBeat, response.meta)
    session.heart_beat(_last_process_time)
    if now - resp.milli_seconds > 10:
        logger.warning("rpc_heartbeat delay:%dms" % (now - resp.milli_seconds))
    pass
