from abc import ABC, abstractmethod
from koala.meta.rpc_meta import *


@register_interface
class Interface1(ABC):
    @rpc_method
    @abstractmethod
    def f1(self):
        pass

    @abstractmethod
    def f2(self):
        pass


@register_interface
class Interface2(ABC):
    @rpc_method
    @abstractmethod
    def f3(self):
        pass

    @abstractmethod
    def f4(self):
        pass


@register_interface
class Interface3(ABC):
    @abstractmethod
    def f5(self):
        pass


@register_interface
class Interface4(ABC):
    @abstractmethod
    def f6(self):
        pass


@register_impl(Interface1)
class Impl1(Interface1):
    def __init__(self):
        pass

    def f1(self):
        pass

    def f2(self):
        pass


@register_impl(Interface2)
class Impl2(Interface2):
    def __init__(self):
        pass

    def f3(self):
        pass

    def f4(self):
        pass


@register_impl(Interface3)
@register_impl(Interface4)
class ImplMix(Interface3, Interface4):
    def __init__(self):
        pass

    def f5(self):
        pass

    def f6(self):
        pass


class TestInterfaceMap(object):
    def test_interface(self):
        assert is_interface(Interface1)
        assert is_interface(Interface2)
        assert is_interface(Interface3)
        assert not is_interface(str)


class TestImplMap(object):
    def test_impl(self):
        assert get_impl_type(Interface1) == Impl1
        assert get_impl_type(Interface2) == Impl2
        assert get_impl_type(Interface3) == ImplMix
        assert get_impl_type(Interface4) == ImplMix
        assert get_impl_type(str) is None


class TestRpcMethod(object):
    def test_rpc_method(self):
        assert get_rpc_method("Interface1.f1") == Interface1.f1
        assert get_rpc_method("Interface2.f4") is None
        assert get_rpc_impl_method("Interface1.f1") == Impl1.f1
        pass


