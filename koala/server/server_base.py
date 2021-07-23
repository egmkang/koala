import asyncio
from koala.server.rpc_meta import build_meta_info
from koala.network.constant import CODEC_RPC
import time
import traceback
from koala.typing import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.network.tcp_server import TcpServer
from koala.network import event_handler
from koala.logger import logger, init_logger
from koala.placement.placement import get_placement_impl
from koala.message import RpcRequest, RpcResponse, RequestHeartBeat, ResponseHeartBeat, NotifyNewActorMessage, \
    NotifyActorSessionAborted, NotifyNewActorSession, RequestAccountLogin
from koala.server.rpc_message_dispatch import process_rpc_request, process_rpc_response, \
    process_heartbeat_request, process_heartbeat_response, update_process_time
from koala.server.gateway_message_dispatch import process_gateway_actor_session_aborted, \
    process_gateway_new_actor_message, process_gateway_new_actor_session, process_gateway_account_login
from koala.server.rpc_request_id import set_request_id_seed
from koala.server.actor_manager import ActorManager
from koala.koala_config import get_config


_socket_session_manager: SocketSessionManager = SocketSessionManager()
_user_message_handler_map: Dict[MessageType,
                                Callable[[SocketSession, object], Coroutine]] = {}
_user_socket_close_handler_map: Dict[MessageType,
                                     Callable[[SocketSession], None]] = {}
_tcp_server: TcpServer = TcpServer()
_actor_manager = ActorManager()


def register_user_handler(cls: MessageType, handler: Callable[[SocketSession, object], Coroutine]):
    if cls in _user_message_handler_map:
        logger.warning("register_user_handler, Type:%s exists" % str(cls))
    _user_message_handler_map[cls] = handler
    pass


def register_user_socket_closed_handler(cls: MessageType, handler: Callable[[SocketSession], None]):
    if cls in _user_socket_close_handler_map:
        logger.warning(
            "register_user_socket_close_handler, Type:%s exists" % str(cls))
    _user_socket_close_handler_map[cls] = handler
    pass


async def _message_handler(session: SocketSession, clz: Type, msg: object):
    t = clz
    if t not in _user_message_handler_map:
        logger.error(
            "process user message, Type:%s not found a processor" % str(t))
        return
    handler: Callable[[SocketSession, object],
                      Coroutine] = _user_message_handler_map[t]
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
    register_user_handler(RequestHeartBeat, process_heartbeat_request)
    register_user_handler(ResponseHeartBeat, process_heartbeat_response)
    # 网关消息和集群内的消息
    register_user_handler(RequestAccountLogin, process_gateway_account_login)
    register_user_handler(NotifyNewActorSession,
                          process_gateway_new_actor_session)
    register_user_handler(NotifyActorSessionAborted,
                          process_gateway_actor_session_aborted)
    register_user_handler(NotifyNewActorMessage,
                          process_gateway_new_actor_message)
    # 在这边可以初始化内置的消息处理器
    # 剩下的消息可以交给用户自己去处理
    event_handler.register_message_handler(_message_handler)
    event_handler.register_socket_close_handler(_socket_close_handler)
    pass


async def _run_placement():
    impl = get_placement_impl()
    if impl is None:
        logger.error("Placement module not initialized")
        return

    try:
        await impl.register_server()
    except Exception as e:
        logger.error("register server fail, Exception:%s" % e)

    while True:
        try:
            await impl.placement_loop()
        except Exception as e:
            await asyncio.sleep(1.0)
            logger.error("run placement fail, Exception:%s, StackTrace:%s" % (
                e, traceback.format_exc()))
    pass


def init_server(globals_dict: dict):
    _config = get_config()
    init_logger(_config.log_name, _config.log_level, not _config.console_log)

    build_meta_info(globals_dict)
    _init_internal_message_handler()
    _time_offset_of = 1626245658    # 随便找了一个时间戳, 可以减小request id序列化的大小
    set_request_id_seed(int(time.time() - _time_offset_of))


def listen(port: int, codec_id: int):
    _tcp_server.create_task(_tcp_server.listen(port, codec_id))


def listen_rpc(port: int):
    _tcp_server.create_task(_tcp_server.listen(port, CODEC_RPC))


def create_task(co):
    _tcp_server.create_task(co)


def run_server():
    _config = get_config()
    if _config.port:
        listen_rpc(_config.port)
    _tcp_server.create_task(update_process_time())
    _tcp_server.create_task(_socket_session_manager.run())
    _tcp_server.create_task(_run_placement())
    _tcp_server.create_task(_actor_manager.gc_loop())
    _tcp_server.run()
