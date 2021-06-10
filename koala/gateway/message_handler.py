import asyncio
import traceback
from koala.message.gateway import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.gateway.codec_gateway import *
from koala.gateway.client_session import *
from koala.placement.placement import PlacementInjection
from koala.logger import logger


_session_manager = SocketSessionManager()
_session_factory = GatewayClientSessionFactory()
_placement = PlacementInjection()


async def _process_gateway_incoming_message_slow(session: SocketSession, msg: bytes, first: bool):
    try:
        user_data = cast(IGatewayClientSession, session.user_data())
        if first:
            data = _session_factory.new_session(msg)
            assert data
            user_data = data
            session.set_user_data(user_data)
        service_type, actor_id = user_data.destination()
        node = _placement.impl.find_position_in_cache(service_type, actor_id)
        if node is None:
            _placement.impl.remove_position_cache(service_type, actor_id)
            node = await _placement.impl.find_position(service_type, actor_id)
        if node is None:
            logger.warning("IncomingMessageSlow, Actor:%s/%s cannot find position" % (service_type, actor_id))
            return

        if node.session is None:
            logger.warning("IncomingMessageSlow, Actor:%s/%s drop data" % (service_type, actor_id))
            return
        if first:
            new_connection = NotifyConnectionComing()
            new_connection.session_id = session.session_id
            new_connection.service_type = service_type
            new_connection.actor_id = actor_id
            new_connection.token = msg
            message: object = new_connection
            pass
        else:
            new_message = NotifyNewMessage()
            new_message.service_type = service_type
            new_message.actor_id = actor_id
            new_message.session_id = session.session_id
            new_message.message = msg
            message = new_message
            pass
        await node.session.send_message(message)
    except Exception as e:
        logger.error("run placement fail, Exception:%s, StackTrace:%s" % (e, traceback.format_exc()))
    pass


async def process_gateway_incoming_message(session: SocketSession, message: object):
    msg = cast(GatewayRawMessage, message)
    user_data = cast(IGatewayClientSession, session.user_data())
    if user_data is None:
        asyncio.create_task(_process_gateway_incoming_message_slow(session, msg.data, True))
        return
    service_type, actor_id = user_data.destination()
    node = _placement.impl.find_position_in_cache(service_type, actor_id)
    if node is None:
        asyncio.create_task(_process_gateway_incoming_message_slow(session, msg.data, False))
        return

    if not node.session:
        logger.warning("IncomingMessage, Actor:%s/%s, proxy is none, drop data" % (service_type, actor_id))
        return
    new_message = NotifyNewMessage()
    new_message.service_type = service_type
    new_message.actor_id = actor_id
    new_message.session_id = session.session_id
    new_message.message = msg.data
    await node.session.send_message(new_message)


async def process_gateway_send_message(session: SocketSession, msg: object):
    req = cast(RequestSendMessageToPlayer, msg)
    if req.session_ids is not None:
        for session_id in req.session_ids:
            client = _session_manager.get_session(session_id)
            if client is not None:
                await client.send_message(req.message)
    if req.session_id != 0:
        client = _session_manager.get_session(req.session_id)
        if client is not None:
            await client.send_message(req.message)
    pass


async def process_gateway_change_destination(session: SocketSession, msg: object):
    req = cast(RequestChangeMessageDestination, msg)
    client = _session_manager.get_session(req.session_id)
    if client is not None:
        if client.user_data() is not None:
            user_data = cast(IGatewayClientSession, client.user_data())
            user_data.change_destination(req.new_service_type, req.new_actor_id)
            logger.info("ChangeDestination, SessionID:%d, NewActor:%s/%s" % (req.session_id, req.new_service_type, req.new_actor_id))
        else:
            logger.info("ChangeDestination, SessionID:%d use_data is none" % req.session_id)
    else:
        logger.warning("ChangeDestination, SessionID:%d not found" % req.session_id)
    pass


async def process_gateway_close_connection(session: SocketSession, msg: object):
    req = cast(RequestCloseConnection, msg)
    client = _session_manager.get_session(req.session_id)
    # TODO
    # 这个service type用来做路由, 如果不是主Actor, 是不需要关闭的
    logger.info("CloseConnection, SessionID:%d" % req.session_id)
    if client is not None:
        client.close()
    pass


