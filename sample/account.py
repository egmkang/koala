from koala.typing import *
from koala.logger import logger
from koala.message import RpcMessage, RequestAccountLogin, ResponseAccountLogin
from koala.network.socket_session import SocketSession
from koala.server.actor_base import ActorBase
from koala.check_sum import message_check_sum
from koala.koala_config import KoalaConfig, get_config
from sample.interfaces import IAccount


_config: Optional[KoalaConfig] = None


class EmptyAccount(IAccount, ActorBase):
    def __init__(self):
        super(EmptyAccount, self).__init__()
    pass


async def process_gateway_account_login(session: SocketSession, msg: object):
    global _config
    if not _config:
        _config = get_config()

    request = cast(RpcMessage, msg)
    req = cast(RequestAccountLogin, request.meta)
    body = request.body
    body_message, check_sum = message_check_sum(
        body, private_key=_config.private_key)
    logger.info("process_gateway_account_login, SessionID:%s, OpenID:%s, ServerUD:%s , CheckSum:%s, %s" %
                (req.session_id, req.open_id, req.server_id, check_sum, body_message))

    resp = ResponseAccountLogin()
    resp.session_id = req.session_id
    resp.actor_type = body_message.get("actor_type", "IPlayer")
    resp.actor_id = body_message.get("actor_id", "1")
    await session.send_message(RpcMessage(meta=resp))
