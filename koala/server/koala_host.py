import asyncio
import time
import traceback
from koala.typing import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.network.tcp_server import TcpServer
from koala.network import event_handler
from koala.logger import logger, init_logger
from koala.placement.placement import Placement
from koala.message import RpcRequest, RpcResponse, RequestHeartBeat, ResponseHeartBeat, NotifyNewActorMessage, \
    NotifyActorSessionAborted, NotifyNewActorSession, RequestAccountLogin
from koala.server import rpc_message_dispatch, gateway_message_dispatch, rpc_request_id, rpc_meta
from koala.server.actor_manager import ActorManager
from koala import koala_config
from koala.server.fastapi import *
from koala.network.constant import CODEC_RPC
from koala.placement.placement import *
from koala.pd.placement import *

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
    register_user_handler(RpcRequest, rpc_message_dispatch.process_rpc_request)
    register_user_handler(
        RpcResponse, rpc_message_dispatch.process_rpc_response)
    register_user_handler(
        RequestHeartBeat, rpc_message_dispatch.process_heartbeat_request)
    register_user_handler(
        ResponseHeartBeat, rpc_message_dispatch.process_heartbeat_response)
    # 网关消息和集群内的消息
    register_user_handler(
        RequestAccountLogin, gateway_message_dispatch.process_gateway_account_login)
    register_user_handler(NotifyNewActorSession,
                          gateway_message_dispatch.process_gateway_new_actor_session)
    register_user_handler(NotifyActorSessionAborted,
                          gateway_message_dispatch.process_gateway_actor_session_aborted)
    register_user_handler(NotifyNewActorMessage,
                          gateway_message_dispatch.process_gateway_new_actor_message)
    # 在这边可以初始化内置的消息处理器
    # 剩下的消息可以交给用户自己去处理
    event_handler.register_message_handler(_message_handler)
    event_handler.register_socket_close_handler(_socket_close_handler)
    pass


async def _run_placement():
    impl = Placement.instance()
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


def init_server(globals_dict: Dict, config_file_name: str = ""):
    # 需要注入config实现, 需要在初始化服务器之前注入
    _config = koala_config.get_config()
    if config_file_name:
        _config.parse(config_file_name)
    init_logger(_config.log_name, _config.log_level, not _config.console_log)

    rpc_meta.build_meta_info(globals_dict)
    _init_internal_message_handler()
    _time_offset_of = 1626245658    # 随便找了一个时间戳, 可以减小request id序列化的大小
    rpc_request_id.set_request_id_seed(int(time.time() - _time_offset_of))


def use_pd(pd_impl: Optional[Placement] = None):
    if not pd_impl:
        pd_impl = PDPlacementImpl()
    Placement.set_instance(pd_impl)


def listen(port: int, codec_id: int):
    _tcp_server.create_task(_tcp_server.listen(port, codec_id))


def listen_rpc(port: int):
    _tcp_server.create_task(_tcp_server.listen(port, CODEC_RPC))


def listen_fastapi(*args, **kwargs):
    if "host" not in kwargs:
        kwargs["host"] = "0.0.0.0"
    if "port" not in kwargs:
        port = koala_config.get_config().fastapi_port
        kwargs["port"] = port

    _tcp_server.create_task(fastapi_serve(*args, **kwargs))


def create_task(co):
    _tcp_server.create_task(co)


async def _try_update_load_loop():
    impl = Placement.instance()
    last = 0
    while True:
        await asyncio.sleep(10)
        try:
            v = _actor_manager.weight
            if last != v:
                logger.info("ActorWeight:%d" % v)
                last = v
            impl.set_load(last)
        except:
            pass


def run_server():
    _config = koala_config.get_config()
    if _config.port:
        listen_rpc(_config.port)
    _tcp_server.create_task(rpc_message_dispatch.update_process_time())
    _tcp_server.create_task(_socket_session_manager.run())
    _tcp_server.create_task(_run_placement())
    _tcp_server.create_task(_actor_manager.gc_loop())
    _tcp_server.create_task(_actor_manager.calc_weight_loop())
    _tcp_server.create_task(_try_update_load_loop())
    _tcp_server.run()
