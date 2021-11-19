import asyncio
import time
from koala.typing import *
from koala.logger import logger
from koala.singleton import Singleton
from koala.server.rpc_meta import get_impl_type, get_interface_type
from koala.server.rpc_exception import RpcException
from koala.server.actor_base import ActorBase
from koala.server.actor_context import ActorContext


ActorType = TypeVar("ActorType", bound=ActorBase)
EntityDictType = Dict[Type, Dict[ActorID, ActorBase]]


def _new_actor(impl_type: Type[ActorType], uid: ActorID) -> ActorBase:
    if impl_type is None:
        raise Exception("ImplType is None")
    actor: ActorBase = impl_type()
    actor._init_actor(uid, ActorContext())
    return actor


# 逻辑层不允许使用这个类
class ActorManager(Singleton):
    def __init__(self):
        super(ActorManager, self).__init__()
        self.__dict: EntityDictType = dict()
        self.__weight: int = 0

    @property
    def weight(self) -> int:
        return self.__weight

    def get_entity(self, i_type: Type[ActorType], uid: ActorID) -> Optional[ActorBase]:
        impl_type = get_impl_type(i_type)
        if impl_type in self.__dict:
            d = self.__dict[impl_type]
            if uid in d:
                return d[uid]
        return None

    def get_or_new(self, i_type: Type[ActorType], uid: ActorID) -> ActorBase:
        impl_type = get_impl_type(i_type)
        if not impl_type:
            raise Exception("interface %s not found an impl" % i_type)
        if impl_type not in self.__dict:
            self.__dict[impl_type] = dict()
        actor_dict = self.__dict[impl_type]
        uid = impl_type.actor_uid_type()(uid)
        if uid not in actor_dict:
            # create here
            actor = _new_actor(cast(Type[ActorType], impl_type), uid)
            actor_dict[uid] = actor
            return actor
        return actor_dict[uid]

    def get_or_new_by_name(self, actor_type: str, uid: ActorID) -> ActorBase:
        i_type = get_interface_type(actor_type)
        if i_type is None:
            raise RpcException.interface_invalid()
        return self.get_or_new(i_type, uid)

    # (ActorBase) -> Bool
    # true继续遍历
    # false中断
    def for_each(self, i_type: Type, fn: Callable[[ActorBase], bool]):
        if i_type not in self.__dict:
            return
        d: Dict[ActorID, ActorBase] = self.__dict[i_type]
        for key in d:
            if not fn(d[key]):
                break

    @classmethod
    async def __gc_actors(cls, actors: Dict[ActorID, ActorBase]):
        current_time = time.time()
        need_remove: List[Tuple[ActorID, ActorBase]] = list()
        for actor_id, actor in actors.items():
            if not actor.context or current_time >= actor.context.last_message_time + actor.gc_time():
                need_remove.append((actor_id, actor))
        for actor_id, actor in need_remove:
            if actor.context:
                await actor.context.push_message(None)
            logger.info("gc_actors, Actor:%s/%s" %
                        (actor.type_name, actor.uid))
            actors.pop(actor_id)

    async def calc_weight_loop(self):
        while True:
            await asyncio.sleep(10)
            weight = 0
            for actor_type in self.__dict:
                actors = self.__dict[actor_type]
                for actor_id in actors:
                    actor = actors[actor_id]
                    weight += actor.actor_weight() * len(actors)
                    break
            self.__weight = weight

    # 这边需要把很长时间没有活跃的actor给gc掉
    async def gc_loop(self):
        while True:
            await asyncio.sleep(60)
            logger.trace("actor_gc_loop")
            for actor_type in self.__dict:
                try:
                    await self.__gc_actors(self.__dict[actor_type])
                except:
                    pass
