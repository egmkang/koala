import traceback
import weakref
from abc import ABC
from koala.membership.membership_manager import MembershipManager
from koala.message import RpcMessage, NotifyActorSessionAborted, NotifyNewActorMessage, NotifyNewActorSession
from koala.typing import *
from koala.logger import logger
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.server.actor_context import ActorContext
from koala.server.rpc_proxy import get_rpc_proxy


_session_manager = SocketSessionManager()
_membership = MembershipManager()


async def _send_message(session_id: int, msg: object):
    session = _session_manager.get_session(session_id)
    if session:
        await session.send_message(msg)


class ActorBase(ABC):
    def __init__(self):
        self.__gateway_session_id = 0
        self.__uid = 0
        self.__context = None
        self.__socket_session: Optional[weakref.ReferenceType[SocketSession]] = None
        pass

    def _init_actor(self, uid: object, context: ActorContext):
        self.__uid = uid
        self.__context = context
        pass

    @property
    def type_name(self):
        return type(self).__qualname__

    @property
    def uid(self) -> object:
        return self.__uid

    @property
    def context(self) -> ActorContext:
        return self.__context

    def gateway_server_id(self, gateway_session_id: int) -> int:
        return gateway_session_id // 10_000_000_000

    def set_session_id(self, session_id: int):
        old_session = self.__gateway_session_id
        self.__gateway_session_id = session_id
        gateway_server = self.gateway_server_id(self.__gateway_session_id)
        node = _membership.get_member(gateway_server)
        socket_session = node.session if node else None
        if socket_session:
            self.__socket_session = weakref.ref(socket_session)
        self.on_session_changed(old_session)

    def on_session_changed(self, old_session_id: int):
        logger.info("Actor:%s/%s, OldSessionID:%s, NewSessionID:%s" %
                    (self.type_name, self.uid, old_session_id, self.session_id))

    @property
    def session_id(self) -> int:
        return self.__gateway_session_id

    @property
    def _socket(self) -> Optional[SocketSession]:
        if self.__socket_session is not None:
            return self.__socket_session()
        return None

    async def activate_async(self):
        try:
            await self.on_activate_async()
        except Exception as e:
            logger.error("Actor.OnActivateAsync, Actor:%s/%s, Exception:%s, StackTrace:%s" %
                         (self.type_name, self.uid, e, traceback.format_exc()))

    async def deactivate_async(self):
        try:
            await self.on_deactivate_async()
        except Exception as e:
            logger.error("Actor.OnDeactivateAsync, Actor:%s/%s, Exception:%s, StackTrace:%s" %
                         (self.type_name, self.uid, e, traceback.format_exc()))

    async def on_activate_async(self):
        pass

    async def on_deactivate_async(self):
        pass

    async def send_message(self, msg: object, session_id=0):
        socket_session = self._socket
        if session_id != 0:
            session = _session_manager.get_session(session_id)
            if session:
                socket_session = session
        if socket_session:
            await socket_session.send_message(msg)
        else:
            logger.warning("Actor.SendMessage, Actor:%s/%s , SocketSession not found" % (self.type_name, self.uid))

    async def dispatch_message(self, msg: object) -> None:
        try:
            if isinstance(msg, RpcMessage):
                rpc_message = cast(RpcMessage, msg)
                if isinstance(rpc_message.meta, NotifyNewActorMessage):
                    await self.dispatch_user_message(msg)
                elif isinstance(rpc_message.meta, NotifyNewActorSession):
                    await self.on_new_session(rpc_message.meta, rpc_message.body)
                elif isinstance(rpc_message.meta, NotifyActorSessionAborted):
                    await self.on_session_aborted(rpc_message.meta)
            else:
                await self.dispatch_user_message(msg)
        except Exception as e:
            logger.error("Actor:%s/%s dispatch_message Exception:%s" % (self.type_name, self.uid, e))

    async def dispatch_user_message(self, msg: object) -> None:
        """
        用户需要自己处理的消息

        不要抛出异常!!!

        不要抛出异常!!!

        不要抛出异常!!!

        :param msg: 用户自定义消息
        """
        pass

    async def on_new_session(self, msg: NotifyNewActorSession, body: bytes):
        logger.info("Actor:%s/%s NewSessionID:%s" % (self.type_name, self.uid, msg.session_id))
        self.set_session_id(msg.session_id)
        pass

    async def on_session_aborted(self, msg: NotifyActorSessionAborted):
        logger.info("Actor:%s/%s SessionID:%s aborted" % (self.type_name, self.uid, self.session_id))
        self.set_session_id(0)

    def get_proxy(self, actor_type: Type[T], uid: object) -> T:
        o = get_rpc_proxy(actor_type, uid, self.context)
        return cast(T, o)
