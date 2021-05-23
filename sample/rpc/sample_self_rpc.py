import asyncio
import random
from abc import ABC, abstractmethod
from koala.server import server_base
from koala.server.actor_base import ActorBase
from koala.meta.rpc_meta import *
from koala.network.socket_session import SocketSessionManager
from koala.placement.placement import PlacementInjection
from koala.server.rpc_proxy import get_rpc_proxy
from koala.logger import logger
from sample.rpc.placement_impl import RpcSelfPlacement


_session_manager = SocketSessionManager()


@rpc_interface
class IService1(ABC):
    @abstractmethod
    async def say_hello(self, hello: str) -> str:
        pass

    @abstractmethod
    async def say(self):
        pass

    @abstractmethod
    async def reentrancy(self) -> object:
        pass


@rpc_interface
class IService2(ABC):
    @abstractmethod
    async def hello(self, my_id: object, times: int) -> str:
        pass


@rpc_impl(IService1)
class Service1Impl(IService1, ActorBase):
    def __init__(self):
        super(Service1Impl, self).__init__()

    async def say_hello(self, hello: str) -> str:
        service_2 = self.get_proxy(IService2, "2")
        logger.info("service 2 return %s" % service_2.hello(self.uid, random.randrange(0, 10000)))
        return "my name is %s, and yours is %s" % (self.uid, hello)

    async def say(self):
        pass

    async def reentrancy(self) -> object:
        return self.uid


@rpc_impl(IService2)
class Service2Impl(IService2, ActorBase):
    def __init__(self):
        super(Service2Impl, self).__init__()

    async def hello(self, my_id: object, times: int) -> str:
        proxy = self.get_proxy(IService1, my_id)
        return "hello world %d, reentrancy: %s" % (times, await proxy.reentrancy())


async def service_1():
    await asyncio.sleep(3.0)
    proxy = get_rpc_proxy(IService1, "1")
    logger.info(await proxy.say_hello("2"))
    pass


@rpc_interface
class IBench(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def echo(self, e: str) -> str:
        pass


@rpc_impl(IBench)
class BenchImpl(IBench, ActorBase):
    def __init__(self):
        pass

    def echo(self, e: str) -> str:
        return e


finished = 0


def bench(index: object):
    global finished
    gevent.sleep(3)
    proxy = get_rpc_proxy(IBench, index)
    while True:
        r = proxy.echo("12121212")
        finished += 1


def qps():
    last = 0
    while True:
        gevent.sleep(1.0)
        v = finished
        if v - last > 0:
            logger.info("QPS:%d" % (v - last))
            last = v


placement = RpcSelfPlacement(5555, [IService1.__qualname__, IService2.__qualname__])
PlacementInjection().set_impl(placement)


server_base.init_server()
server_base.listen_rpc(5555)

gevent.spawn(lambda: service_1())

for item in range(1):
    i = item
    gevent.spawn(lambda: bench(i))
gevent.spawn(lambda: qps())

server_base.run_server()
