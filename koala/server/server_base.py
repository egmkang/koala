import asyncio
import time
import traceback
from koala.typing import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.network.tcp_server import TcpServer
from koala.network import event_handler
from koala.logger import logger
from koala.placement.placement import PlacementInjection
from koala.message.rpc import RpcRequest, RpcResponse
from koala.message.message import HeartBeatRequest, HeartBeatResponse
from koala.message.gateway import NotifyNewMessage, NotifyConnectionAborted, NotifyConnectionComing, \
                                    RequestCloseConnection, RequestChangeMessageDestination, RequestSendMessageToPlayer
from koala.server.rpc_message_dispatch import process_rpc_request, process_rpc_response, \
                                                process_heartbeat_request, process_heartbeat_response
from koala.server.gateway_message_dispatch import process_gateway_connection_aborted, process_gateway_new_message, \
                                                    process_gateway_connection_coming
from koala.server.rpc_request_id import set_request_id_seed
from koala.gateway.message_handler import process_gateway_send_message, process_gateway_change_destination, \
                                            process_gateway_close_connection, process_gateway_incoming_message
from koala.gateway.codec_gateway import GatewayRawMessage


T = TypeVar("T")
_socket_session_manager: SocketSessionManager = SocketSessionManager()
_user_message_handler_map: {T: Callable[[SocketSession, object], Coroutine]} = {}
_user_socket_close_handler_map: {T: Callable[[SocketSession], None]} = {}
_tcp_server: TcpServer = TcpServer()


def register_user_handler(cls: T, handler: Callable[[SocketSession, object], Coroutine]):
    if cls in _user_message_handler_map:
        logger.warning("register_user_handler, Type:%s exists" % str(cls))
    _user_message_handler_map[cls] = handler
    pass


def register_user_socket_closed_handler(cls: T, handler: Callable[[SocketSession], None]):
    if cls in _user_socket_close_handler_map:
        logger.warning("register_user_socket_close_handler, Type:%s exists" % str(cls))
    _user_socket_close_handler_map[cls] = handler
    pass


async def _message_handler(session: SocketSession, msg: object):
    t = msg.__class__
    if t not in _user_message_handler_map:
        logger.error("process user message, Type:%s not found a processor" % str(t))
        return
    handler: Callable[[SocketSession, object], Coroutine] = _user_message_handler_map[t]
    await handler(session, msg)


def _socket_close_handler(session: SocketSession):
    t = session.user_data().__class__
    if t not in _user_socket_close_handler_map:
        return
    handler = _user_socket_close_handler_map[t]
    handler(session)
    pass


def _init_internal_message_handler():
    register_user_handler(RpcRequest, process_rpc_request)
    register_user_handler(RpcResponse, process_rpc_response)
    register_user_handler(HeartBeatRequest, process_heartbeat_request)
    register_user_handler(HeartBeatResponse, process_heartbeat_response)
    # 网关消息和集群内的消息
    register_user_handler(NotifyConnectionAborted, process_gateway_connection_aborted)
    register_user_handler(NotifyConnectionComing, process_gateway_connection_coming)
    register_user_handler(NotifyNewMessage, process_gateway_new_message)
    register_user_handler(RequestChangeMessageDestination, process_gateway_change_destination)
    register_user_handler(RequestSendMessageToPlayer, process_gateway_send_message)
    register_user_handler(RequestCloseConnection, process_gateway_close_connection)
    # 客户端传入的消息
    register_user_handler(GatewayRawMessage, process_gateway_incoming_message)
    # 在这边可以初始化内置的消息处理器
    # 剩下的消息可以交给用户自己去处理

    event_handler.register_message_handler(_message_handler)
    event_handler.register_socket_close_handler(_socket_close_handler)
    pass


async def _run_placement():
    impl = PlacementInjection().impl
    if impl is None:
        logger.error("Placement module not initialized")
        return

    impl.register_server()
    while True:
        try:
            await impl.placement_loop()
        except Exception as e:
            await asyncio.sleep(1.0)
            logger.error("run placement fail, Exception:%s" % traceback.format_exc())
            pass
    pass


def init_server():
    _init_internal_message_handler()
    _time_offset_of = 1612333986    # 随便找了一个世间戳, 可以减小request id序列化的大小
    set_request_id_seed(int(time.time() - _time_offset_of))


def listen(port: int, codec_id: int):
    _tcp_server.listen(port, codec_id)
    pass


def run_server():
    _tcp_server.create_task(_socket_session_manager.run())
    _tcp_server.create_task(_run_placement())
    _tcp_server.run()
