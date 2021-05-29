import asyncio
import time
from koala.typing import *
from koala.message.rpc import RpcRequest, RpcResponse
from koala.message.message import HeartBeatRequest, HeartBeatResponse
from koala.meta.rpc_meta import *
from koala.server.rpc_future import *
from koala.server.actor_message_loop import _send_error_resp, \
                                            dispatch_actor_message,\
                                            run_actor_message_loop
from koala.server.actor_base import *
from koala.server.entity_manager import EntityManager
from koala.server.rpc_exception import RpcException
from koala.placement.placement import PlacementInjection


_entity_manager = EntityManager()
_placement = PlacementInjection()


async def process_rpc_request_slow(proxy: SocketSession, request: object):
    placement = _placement.impl
    req: RpcRequest = cast(RpcRequest, request)
    placement.remove_position_cache(req.service_name, req.actor_id)
    try:
        node = await placement.find_position(req.service_name, req.actor_id)
        if node is not None and node.server_uid == placement.server_id():
            actor = _entity_manager.get_or_new_by_name(req.service_name, req.actor_id)
            if actor is None:
                raise RpcException.entity_not_found()
            run_actor_message_loop(actor)
            await dispatch_actor_message(actor, proxy, req)
        else:
            await _send_error_resp(proxy, req.request_id, RpcException.position_changed())
    except Exception as e:
        logger.error("process_rpc_request, Exception:%s" % traceback.format_exc())
        await _send_error_resp(proxy, req.request_id, e)
    pass


async def process_rpc_request(proxy: SocketSession, request: object):
    req: RpcRequest = cast(RpcRequest, request)
    try:
        node = _placement.impl.find_position_in_cache(req.service_name, req.actor_id)
        # rpc请求方, 和自己的pd缓存一定要是一致的
        # 否则就清掉自己的缓存, 然后重新查找一下定位
        if node is not None and node.server_uid == _placement.impl.server_id() \
                and req.server_id == _placement.impl.server_id():
            actor = _entity_manager.get_or_new_by_name(req.service_name, req.actor_id)
            if actor is None:
                raise RpcException.entity_not_found()
            run_actor_message_loop(actor)
            await dispatch_actor_message(actor, proxy, req)
        else:
            asyncio.create_task(process_rpc_request_slow(proxy, request))
    except Exception as e:
        logger.error("process_rpc_request, Exception:%s" % traceback.format_exc())
        await _send_error_resp(proxy, req.request_id, e)
    pass


async def process_rpc_response(session: SocketSession, response: object):
    resp: RpcResponse = cast(RpcResponse, response)
    future: AsyncResult = get_future(resp.request_id)
    if resp.error_code != 0:
        future.set_exception(Exception(resp.error_str))
    else:
        future.set_result(resp.response)


async def process_heartbeat_request(proxy: SocketSession, request: object):
    req: HeartBeatRequest = cast(HeartBeatRequest, request)
    resp = HeartBeatResponse()
    resp.milli_seconds = req.milli_seconds
    await proxy.send_message(resp)
    logger.trace("process_rpc_heartbeat_request, SessionID:%d" % proxy.session_id)


async def process_heartbeat_response(session: SocketSession, response: object):
    now = int(time.time() * 1000)
    resp: HeartBeatResponse = cast(HeartBeatResponse, response)
    if now - resp.milli_seconds > 10:
        logger.warning("rpc_heartbeat delay:%dms" % (now - resp.milli_seconds))
    pass
