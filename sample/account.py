from koala.typing import *
from koala.logger import logger
from koala.json_util import json_loads
from koala.message import RpcMessage, RequestAccountLogin
from koala.meta.rpc_meta import rpc_impl
from koala.network.socket_session import SocketSession
from koala.server.actor_base import ActorBase
from sample.interfaces import IAccount


@rpc_impl(IAccount)
class EmptyAccount(IAccount, ActorBase):
    def __init__(self):
        super(EmptyAccount, self).__init__()
    pass


async def process_gateway_account_login(session: SocketSession, msg: object):
    request = cast(RpcMessage, msg)
    req = cast(RequestAccountLogin, request.meta)
    body = request.body
    body_message: dict = json_loads(body)
    logger.info("process_gateway_account_login, SessionID:%s, OpenID:%s, ServerUD:%s , %s" %
                (req.session_id, req.open_id, req.server_id, body_message))
    pass
