import time
import traceback
import weakref
from abc import ABC, abstractmethod
from koala.server.actor_interface import ActorInterface, ActorInterfaceType
from koala.membership.membership_manager import MembershipManager
from koala.message import RpcMessage, NotifyActorSessionAborted, NotifyNewActorMessage, NotifyNewActorSession
from koala.typing import *
from koala.logger import logger
from koala.network.socket_session import SocketSession, SocketSessionManager
from koala.server.actor_context import ActorContext
from koala.server import rpc_proxy
from koala.server.actor_timer import ActorTimerManager, ActorTimer


_session_manager = SocketSessionManager()
_membership = MembershipManager()


class ActorBase(ActorInterface, ABC):
    def __init__(self):
        super(ActorBase, self).__init__()

        self.__gateway_session_id = 0
        self.__uid = 0
        self.__context: Optional[ActorContext] = None
        self.__socket_session: Optional[weakref.ReferenceType[SocketSession]] = None
        self.__timer_manager = ActorTimerManager(self.weak)
        pass

    def _init_actor(self, uid: ActorID, context: ActorContext):
        self.__uid = self.actor_uid_type()(uid)
        self.__context = context
        pass

    @classmethod
    def gc_time(cls) -> int:
        return 30 * 60      # 默认GC超时时间是30分钟

    @classmethod
    def actor_weight(cls) -> int:
        return 1            # 默认的权重, 系统会按照负载来分配Actor的位置

    @property
    def type_name(self) -> str:
        return type(self).__qualname__

    @classmethod
    def actor_uid_type(cls) -> Type[ActorID]:
        return str

    @property
    def uid(self) -> ActorID:
        return self.__uid

    @property
    def weak(self) -> weakref.ReferenceType["ActorBase"]:
        return weakref.ref(self)

    @property
    def context(self) -> Optional[ActorContext]:
        return self.__context

    def gateway_server_id(self, gateway_session_id: int) -> int:
        _ = self
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
            if self.__timer_manager:
                self.__timer_manager.unregister_all()
                del self.__timer_manager
                self.__timer_manager = None
        except Exception as e:
            logger.error("Actor.OnDeactivateAsync, Actor:%s/%s, Exception:%s, StackTrace:%s" %
                         (self.type_name, self.uid, e, traceback.format_exc()))
            pass
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
            logger.warning(
                "Actor.SendMessage, Actor:%s/%s , SocketSession not found" % (self.type_name, self.uid))

    async def dispatch_message(self, msg: object) -> None:
        try:
            if isinstance(msg, RpcMessage):
                rpc_message = cast(RpcMessage, msg)
                if isinstance(rpc_message.meta, NotifyNewActorMessage):
                    await self.dispatch_user_message(msg)
                elif isinstance(rpc_message.meta, NotifyNewActorSession):
                    await self.on_new_session(rpc_message.meta, rpc_message.body if rpc_message.body else b"{}")
                elif isinstance(rpc_message.meta, NotifyActorSessionAborted):
                    await self.on_session_aborted(rpc_message.meta)
            elif isinstance(msg, ActorTimer):
                msg.tick()
            else:
                await self.dispatch_user_message(msg)
            # 定时器不能延长Actor的生命周期
            if not isinstance(msg, ActorTimer) and self.context:
                self.context.last_message_time = time.time()
        except Exception as e:
            logger.error("Actor:%s/%s dispatch_message Exception:%s" %
                         (self.type_name, self.uid, e))

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
        _ = body
        logger.info("Actor:%s/%s NewSessionID:%s" %
                    (self.type_name, self.uid, msg.session_id))
        self.set_session_id(msg.session_id)
        pass

    async def on_session_aborted(self, msg: NotifyActorSessionAborted):
        _ = msg
        logger.info("Actor:%s/%s SessionID:%s aborted" %
                    (self.type_name, self.uid, self.session_id))
        self.set_session_id(0)

    def get_proxy(self, actor_type: Type[ActorInterfaceType], uid: ActorID) -> ActorInterfaceType:
        o = rpc_proxy.get_rpc_proxy(actor_type, uid, self.context)
        return cast(ActorInterfaceType, o)

    def register_timer(self, interval: int, fn: Callable[[ActorTimer], None]) -> ActorTimer:
        assert self.__timer_manager
        return self.__timer_manager.register_timer(interval, fn)

    def unregister_timer(self, timer_id: int):
        assert self.__timer_manager
        return self.__timer_manager.unregister_timer(timer_id)


class ActorWithIntKey(ActorBase):
    def __init__(self):
        super().__init__()

    @classmethod
    def actor_uid_type(cls) -> Type[ActorID]:
        return int


class ActorWithStrKey(ActorBase):
    def __init__(self):
        super().__init__()

    @classmethod
    def actor_uid_type(cls) -> Type[ActorID]:
        return str
