from koala.rpc_meta import rpc_impl
from koala.typing import *
from koala.message import RpcMessage
from koala.message.gateway import NotifyNewActorMessage, RequestSendMessageToSession, NotifyNewActorSession
from koala.server.actor_base import ActorBase
from koala.check_sum import message_compute_check_sum
from koala.json_util import json_dumps
from koala.conf.config import Config
from sample.interfaces import IPlayer


_config = Config()


@rpc_impl(IPlayer)
class Player(IPlayer, ActorBase):
    def __init__(self):
        super(Player, self).__init__()
        self.__GC_TIME = 30

    def gc_time(self) -> int:
        return self.__GC_TIME

    async def on_new_session(self, msg: NotifyNewActorSession, body: bytes):
        await super(Player, self).on_new_session(msg, body)
        token_message = {'open_id': msg.open_id, "server_id": msg.server_id,
                         "actor_type": "IPlayer", "actor_id": self.uid}
        check_sum = message_compute_check_sum(
            token_message, private_key=_config.private_key)
        token_message["check_sum"] = check_sum

        meta = RequestSendMessageToSession()
        meta.session_id = msg.session_id
        token = json_dumps(token_message)
        await self.send_message(RpcMessage(meta=meta, body=token))

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
