from abc import ABC, abstractmethod
from koala.meta.rpc_meta import *


@rpc_interface
class Interface1(ABC):
    @abstractmethod
    def f1(self):
        pass

    @abstractmethod
    def f2(self):
        pass


@rpc_interface
class Interface2(ABC):
    @abstractmethod
    def f3(self):
        pass

    @abstractmethod
    def f4(self):
        pass


@rpc_interface
class Interface3(ABC):
    @abstractmethod
    def f5(self):
        pass


@rpc_interface
class Interface4(ABC):
    @abstractmethod
    def f6(self):
        pass


@rpc_impl(Interface1)
class Impl1(Interface1):
    def __init__(self):
        pass

    def f1(self):
        pass

    def f2(self):
        pass


@rpc_impl(Interface2)
class Impl2(Interface2):
    def __init__(self):
        pass

    def f3(self):
        pass

    def f4(self):
        pass


@rpc_impl(Interface3)
@rpc_impl(Interface4)
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

    def test_impl(self):
        assert get_impl_type(Interface1) == Impl1
        assert get_impl_type(Interface2) == Impl2
        assert get_impl_type(Interface3) == ImplMix
        assert get_impl_type(Interface4) == ImplMix
        assert get_impl_type(str) is None
