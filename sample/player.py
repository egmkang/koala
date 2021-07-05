from koala.meta.rpc_meta import rpc_impl
from koala.typing import *
from koala.message import RpcMessage
from koala.logger import logger
from koala.message.gateway import NotifyNewActorMessage, RequestSendMessageToSession
from koala.server.actor_base import ActorBase
from sample.interfaces import IPlayer


@rpc_impl(IPlayer)
class Player(IPlayer, ActorBase):
    def __init__(self):
        super(Player, self).__init__()

    async def dispatch_user_message(self, msg: object) -> None:
        rpc_message = cast(RpcMessage, msg)
        # logger.info("dispatch_user_message, meta:%s" % type(rpc_message.meta))
        if isinstance(rpc_message.meta, NotifyNewActorMessage):
            await self.process_new_actor_message(rpc_message.meta, rpc_message.body)

    async def process_new_actor_message(self, msg: NotifyNewActorMessage, body: bytes):
        if msg.session_id != self.session_id:
            self.set_session_id(msg.session_id)
        # logger.info("process_new_actor_message Actor:%s/%s, body:%s" % (self.type_name, self.uid, body))
        meta = RequestSendMessageToSession()
        meta.session_id = self.session_id
        await self.send_message(RpcMessage(meta=meta, body=body))

