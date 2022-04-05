from koala.typing import *
from koala.message import RpcMessage
from koala.message.gateway import (
    NotifyNewActorMessage,
    RequestSendMessageToSession,
    NotifyNewActorSession,
)
from koala.server.actor_base import ActorWithIntKey
from koala import utils, koala_config
from sample.interfaces import IPlayer


_config: Optional[koala_config.KoalaConfig] = None


class Player(IPlayer, ActorWithIntKey):
    def __init__(self):
        super(Player, self).__init__()

    @classmethod
    def gc_time(cls) -> int:
        return 30

    async def echo(self, msg: str) -> str:
        return msg

    async def on_new_session(self, msg: NotifyNewActorSession, body: bytes):
        global _config
        if not _config:
            _config = koala_config.get_config()

        await super(Player, self).on_new_session(msg, body)
        token_message = {
            "open_id": msg.open_id,
            "server_id": msg.server_id,
            "actor_type": "IPlayer",
            "actor_id": self.uid,
        }
        check = utils.message_compute_check_sum(
            token_message, private_key=_config.private_key
        )
        token_message["check_sum"] = check

        meta = RequestSendMessageToSession()
        meta.session_id = msg.session_id
        token = utils.json_dumps(token_message)
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
