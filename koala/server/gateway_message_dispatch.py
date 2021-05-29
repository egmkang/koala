from koala.logger import logger
from koala.message.gateway import *
from koala.placement.placement import PlacementInjection
from koala.server.actor_base import *
from koala.server.entity_manager import EntityManager
from koala.server.rpc_exception import RpcException
from koala.server.actor_message_loop import run_actor_message_loop, dispatch_actor_message


_entity_manager = EntityManager()
_placement = PlacementInjection()


async def _dispatch_user_message_slow(proxy: SocketSession, service_type: str, actor_id: str, msg: object):
    node = await _placement.impl.find_position(service_type, actor_id)
    if node is not None and node.server_uid == _placement.impl.server_id():
        actor = _entity_manager.get_or_new_by_name(service_type, actor_id)
        if actor is None:
            raise RpcException.entity_not_found()
        run_actor_message_loop(actor)
        await dispatch_actor_message(actor, proxy, msg)
        pass
    else:
        if node:
            session = node.session
            if session:
                await session.send_message(msg)
        else:
            logger.warning("Actor:%s/%s, cannot find position" % (service_type, actor_id))
    pass


def _dispatch_user_message(proxy: SocketSession, service_type: str, actor_id: str, msg: object):
    # 这边获取到对象的位置, 然后直接把消息Push到对象Actor的MailBox里面
    # 如果没找到位置, 那么先去定位, 如果不在当前服务器内, 那么帮忙转发到一下
    node = _placement.impl.find_position_in_cache(service_type, actor_id)
    if node is not None and node.server_uid == _placement.impl.server_id():
        actor = _entity_manager.get_or_new_by_name(service_type, actor_id)
        if actor is None:
            raise RpcException.entity_not_found()
        run_actor_message_loop(actor)
        dispatch_actor_message(actor, proxy, msg)
        pass
    else:
        gevent.spawn(lambda: _dispatch_user_message_slow(proxy, service_type, actor_id, msg))
    pass


def process_gateway_connection_coming(proxy: SocketSession, msg: object):
    notify = cast(NotifyConnectionComing, msg)
    _dispatch_user_message(proxy, notify.service_type, notify.actor_id, msg)
    pass


def process_gateway_connection_aborted(proxy: SocketSession, msg: object):
    notify = cast(NotifyConnectionAborted, msg)
    _dispatch_user_message(proxy, notify.service_type, notify.actor_id, msg)
    pass


def process_gateway_new_message(proxy: SocketSession, msg: object):
    notify = cast(NotifyNewMessage, msg)
    _dispatch_user_message(proxy, notify.service_type, notify.actor_id, msg)
    pass

