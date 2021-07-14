from koala.typing import *


__interface_set: Set[Type] = set()
__interface_name_map: Dict[str, Type] = dict()
__impl_map: Dict[Type, Type] = dict()
__impl_name_map: Dict[str, Type] = dict()
__impl_method: Dict[str, Callable] = dict()


def rpc_interface(cls: Type[T]) -> Type[T]:
    __interface_set.add(cls)
    __interface_name_map[cls.__qualname__] = cls
    return cls


def is_interface(cls) -> bool:
    return cls in __interface_set


def get_interface_type(interface_name: str) -> Optional[Type]:
    if interface_name in __interface_name_map:
        return __interface_name_map[interface_name]


def rpc_impl(*interfaces):
    def f(impl: Type[T]) -> Type[T]:
        for interface in interfaces:
            __impl_map[interface] = impl
            __impl_name_map[interface.__qualname__] = impl
        return impl
    return f


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


def get_rpc_impl_method(name: str):
    if name in __impl_method:
        return __impl_method[name]
    interface_name, method_name = name.split('.')
    impl_type = get_impl_type_by_name(interface_name)
    fn = impl_type.__dict__[method_name]
    __impl_method["%s.%s" % (impl_type.__qualname__, method_name)] = fn
    return fn

