import asyncio
import time
import traceback
from koala.typing import *
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.logger import logger


_session_manager = SocketSessionManager()
_last_process_message_time = time.time()
_message_handler: Optional[Callable[[SocketSession, object], Coroutine]] = None
_socket_close_handler: Optional[Callable[[SocketSession], None]] = None


def _process_income_socket(session: SocketSession):
    codec_id = session.codec.codec_id
    _session_manager.add_session(session)
    logger.debug("SocketSessionManager, SessionID:%d added, CodecID:%d" % (session.session_id, codec_id))
    return


def _process_close_socket(session_id: int):
    session = _session_manager.get_session(session_id)
    try:
        if session and _socket_close_handler:
            _socket_close_handler(session)
    except Exception as e:
        logger.error("SocketSessionManager, Before Remove SessionID:%d, Exception:%s" % (session_id, e))
        pass
    if session:
        _session_manager.remove_session(session_id)
        logger.debug("SocketSessionManager, SessionID:%d removed" % session_id)
    return


async def _process_socket_message(session: SocketSession, msg: object):
    try:
        if _message_handler:
            await _message_handler(session, msg)
        else:
            logger.error("process_socket_message, user message handler is None")
    except Exception as e:
        logger.error("process_socket_message, SessionID:%d Exception:%s, StackTrace:%s" %
                     (session.session_id, e, traceback.format_exc()))


def _process_connect_success(session: SocketSession):
    if session:
        session.heart_beat(_last_process_message_time)
        logger.info("SocketSessionManager, SessionID:%d, ConnectSuccess" % session.session_id)
    else:
        logger.error("SocketSessionManager, SessionID:%d not found" % session.session_id)


def register_message_handler(handler: Callable[[SocketSession, object], Coroutine]):
    global _message_handler
    _message_handler = handler
    pass


def register_socket_close_handler(handler: Callable[[SocketSession], None]):
    global _socket_close_handler
    _socket_close_handler = handler
    pass


async def update_message_time():
    global _last_process_message_time
    while True:
        await asyncio.sleep(1.0)
        _last_process_message_time = time.time()


