from koala.typing import *
from koala.singleton import Singleton
from koala.meta.rpc_meta import InstanceType, get_impl_type, get_interface_type
from koala.server.rpc_exception import RpcException
from koala.server.actor_base import ActorBase
from koala.server.actor_context import ActorContext


EntityDictType = Dict[InstanceType, Dict[object, ActorBase]]


def _new_actor(impl_type: InstanceType, uid: object) -> ActorBase:
    if impl_type is None:
        raise Exception("ImplType is None")
    actor: ActorBase = impl_type()
    actor._init_actor(uid, ActorContext())
    return actor


@Singleton
class EntityManager(object):
    def __init__(self):
        self.__dict: EntityDictType = dict()

    def get_entity(self, i_type: Type[InstanceType], uid: object) -> ActorBase:
        impl_type = get_impl_type(i_type)
        if impl_type in self.__dict:
            d = self.__dict[impl_type]
            if uid in d:
                return d[uid]

    def get_or_new(self, i_type: Type[InstanceType], uid: object) -> ActorBase:
        impl_type = get_impl_type(i_type)
        if impl_type not in self.__dict:
            self.__dict[impl_type] = dict()
        d = self.__dict[impl_type]
        if uid not in d:
            # create here
            actor = _new_actor(impl_type, uid)
            d[uid] = actor
            return actor
        return d[uid]

    def get_or_new_by_name(self, service_type: str, uid: object) -> ActorBase:
        i_type = get_interface_type(service_type)
        if i_type is None:
            raise RpcException.interface_invalid()
        return self.get_or_new(i_type, uid)

    # (ActorBase) -> Bool
    # true继续遍历
    # false中断
    def map(self, i_type: Type[InstanceType], fn: Callable[[ActorBase], bool]):
        if i_type not in self.__dict:
            return
        d: Dict[object, ActorBase] = self.__dict[i_type]
        for key in d:
            if not fn(d[key]):
                break

    # TODO
    # 这边需要把很长时间没有活跃的actor给gc掉
    def entity_gc_loop(self):
        pass

