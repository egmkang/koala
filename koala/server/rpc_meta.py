import inspect
import types
import sys
from koala.typing import *
from koala.server.actor_interface import ActorInterface


Interface = TypeVar("Interface", bound=ActorInterface)


__interface_set: Set[Type] = set()
__interface_name_map: Dict[str, Type] = dict()
__impl_map: Dict[Type, Type] = dict()
__impl_name_map: Dict[str, Type] = dict()
__impl_method: Dict[Tuple[str, str], Callable] = dict()


def register_rpc_interface(cls: Type[Interface]):
    __interface_set.add(cls)
    __interface_name_map[cls.__qualname__] = cls


def is_interface(cls: Type[Interface]) -> bool:
    return cls in __interface_set


def get_interface_type(interface_name: str) -> Optional[Type]:
    if interface_name in __interface_name_map:
        return __interface_name_map[interface_name]


def register_rpc_impl(interface_type: Type[Interface], actor_type: Type):
    __impl_map[interface_type] = actor_type
    __impl_name_map[interface_type.__qualname__] = actor_type


def get_impl_type(i_type: Type[T]) -> Optional[Type[T]]:
    if i_type in __impl_map:
        return __impl_map[i_type]


def get_impl_type_by_name(interface_name: str) -> Any:
    if interface_name in __impl_name_map:
        return __impl_name_map[interface_name]


def get_all_impl_types() -> List[Tuple[str, Any]]:
    l: List[Tuple[str, Any]] = list()
    for interface_type in __impl_name_map:
        l.append((interface_type, __impl_name_map[interface_type]))
    return l


def get_all_services() -> Dict[str, str]:
    services: Dict[str, str] = {}
    for (interface_name, impl) in get_all_impl_types():
        services[interface_name] = impl.__qualname__
    return services


def get_rpc_impl_method(name: Tuple[str, str]):
    if name in __impl_method:
        return __impl_method[name]
    impl_type = get_impl_type_by_name(name[0])
    fn = impl_type.__dict__[name[1]]
    __impl_method[name] = fn
    return fn


def build_meta_info(items: Dict):
    interface_set: Set[Type] = set()
    actor_type_set: Set[Type] = set()
    ignore_set = set()

    def check_actor_meta_info(cls: Type):
        from koala.server.actor_base import ActorBase

        if not inspect.isclass(cls):
            return
        if cls == ActorInterface or cls == ActorBase:
            return
        if issubclass(cls, ActorInterface) and not issubclass(cls, ActorBase):
            interface_set.add(cls)
        if issubclass(cls, ActorBase):
            actor_type_set.add(cls)

    def check(val):
        try:
            if isinstance(val, dict) or val in ignore_set:
                return
            ignore_set.add(val)
        except:
            return

        if isinstance(val, types.ModuleType):
            values = inspect.getmembers(val, inspect.isclass)
            for _, v in values:
                check_actor_meta_info(v)
            values = inspect.getmembers(val, inspect.ismodule)
            for _, v in values:
                check(v)
        else:
            check_actor_meta_info(val)

    for _, val in sorted(list(items.items()), reverse=True):
        check(val)

    for interface_type in interface_set:
        for impl_type in actor_type_set:
            if issubclass(impl_type, interface_type):
                register_rpc_interface(interface_type)
                register_rpc_impl(interface_type, impl_type)
    pass
