from koala.meta.rpc_meta import rpc_impl
from koala.typing import *
from koala.message import RpcMessage
from koala.logger import logger
from koala.message.gateway import NotifyNewActorMessage, NotifyNewActorSession, NotifyActorSessionAborted
from koala.server.actor_base import ActorBase
from sample.interfaces import IPlayer


@rpc_impl(IPlayer)
class Player(IPlayer, ActorBase):
    def __init__(self):
        super(Player, self).__init__()

    def get_server_session_id(self) -> Optional[int]:
        return self.session_id // 10_000_000_000

    async def dispatch_user_message(self, msg: object) -> None:
        rpc_message = cast(RpcMessage, msg)
        if isinstance(rpc_message.meta, NotifyNewActorMessage):
            await self.process_new_actor_message(rpc_message.meta, rpc_message.body)
        elif isinstance(rpc_message.meta, NotifyNewActorSession):
            await self.process_new_actor_session(rpc_message.meta, rpc_message.body)
        elif isinstance(rpc_message.meta, NotifyActorSessionAborted):
            await self.process_actor_session_aborted(rpc_message.meta, rpc_message.body)
        else:
            logger.warning("Actor:%s/%s dispatch_user_message, MessageType:%s" %
                           (self.type_name, self.uid, type(rpc_message.meta)))

    async def process_new_actor_message(self, msg: NotifyNewActorMessage, body: bytes):
        pass

    async def process_new_actor_session(self, msg: NotifyNewActorSession, body: bytes):
        pass

    async def process_actor_session_aborted(self, msg: NotifyActorSessionAborted, body: bytes):
        pass
