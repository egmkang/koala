from abc import ABC, abstractmethod
from koala import server
from koala.server.rpc_meta import *
from koala.server.actor_interface import ActorInterface
from koala.server.actor_base import ActorBase, ActorWithIntKey, ActorWithStrKey


class Interface1(ActorInterface):
    @abstractmethod
    def f1(self):
        pass

    @abstractmethod
    def f2(self):
        pass


class Interface2(ActorInterface):
    @abstractmethod
    def f3(self):
        pass

    @abstractmethod
    def f4(self):
        pass


class Interface3(ActorInterface):
    @abstractmethod
    def f5(self):
        pass


class Interface4(ActorInterface):
    @abstractmethod
    def f6(self):
        pass


class Impl1(Interface1, ActorBase):
    def __init__(self):
        super(Impl1, self).__init__()
        pass

    def f1(self):
        pass

    def f2(self):
        pass


class Impl2(Interface2, ActorWithStrKey):
    def __init__(self):
        super(Impl2, self).__init__()
        pass

    def f3(self):
        pass

    def f4(self):
        pass


class ImplMix(Interface3, Interface4, ActorWithIntKey):
    def __init__(self):
        super(ImplMix, self).__init__()
        pass

    def f5(self):
        pass

    def f6(self):
        pass


build_meta_info(globals().copy())


def test_interface():
    assert is_interface(Interface1)
    assert is_interface(Interface2)
    assert is_interface(Interface3)
    # assert not is_interface(str)


def test_impl():
    assert get_impl_type(Interface1) == Impl1
    assert get_impl_type(Interface2) == Impl2
    assert get_impl_type(Interface3) == ImplMix
    assert get_impl_type(Interface4) == ImplMix
    assert get_impl_type(str) is None
