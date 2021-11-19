from abc import abstractmethod
import asyncio
import random
from koala.server import koala_host
from koala.server.actor_interface import ActorInterface
from koala.server.actor_base import ActorWithStrKey
from koala.server.rpc_meta import *
from koala.placement.placement import get_placement_impl, set_placement_impl
from koala.pd.simple import SelfHostedPlacement
from koala.server.rpc_proxy import get_rpc_proxy
from koala.server.actor_timer import ActorTimer
from koala.logger import logger


class IService1(ActorInterface):
    @abstractmethod
    async def say_hello(self, hello: str) -> str:
        pass

    async def say(self):
        pass

    async def reentrancy(self) -> object:
        pass


class IService2(ActorInterface):
    @abstractmethod
    async def hello(self, my_id: object, times: int) -> str:
        pass


class Service1Impl(IService1, ActorWithStrKey):
    def __init__(self):
        super(Service1Impl, self).__init__()

    async def say_hello(self, hello: str) -> str:
        service_2 = self.get_proxy(IService2, "2")
        logger.info("service 2 return %s" % await service_2.hello(self.uid, random.randrange(0, 10000)))
        return "my name is %s, and yours is %s" % (self.uid, hello)

    async def say(self):
        pass

    async def reentrancy(self) -> object:
        return self.uid


class Service2Impl(IService2, ActorWithStrKey):
    def __init__(self):
        super(Service2Impl, self).__init__()

    async def hello(self, my_id: ActorID, times: int) -> str:
        proxy = self.get_proxy(IService1, my_id)
        return "hello world %d, reentrancy: %s" % (times, await proxy.reentrancy())


async def service_1():
    await asyncio.sleep(3.0)
    proxy = get_rpc_proxy(IService1, "1")
    logger.info(await proxy.say_hello("2"))
    pass


class IBench(ActorInterface):
    @abstractmethod
    async def echo(self, e: str) -> str:
        pass

    @abstractmethod
    async def run_timer(self, count: int):
        pass


class BenchImpl(IBench, ActorWithStrKey):
    def __init__(self):
        super(BenchImpl, self).__init__()

    async def echo(self, e: str) -> str:
        return e

    async def run_timer(self, count: int):
        weak_actor = self.weak

        def f(timer: ActorTimer):
            logger.info("timer, tick:%s" % timer.tick_count)
            if timer.tick_count >= count:
                a: BenchImpl = cast(BenchImpl, weak_actor())
                a.unregister_timer(timer.timer_id)
        self.register_timer(1000, f)


finished = 0


async def bench(index: ActorID):
    global finished
    await asyncio.sleep(3)
    proxy = get_rpc_proxy(IBench, index)
    while True:
        _ = await proxy.echo("12121212")
        finished += 1


async def run_timer(index: ActorID):
    await asyncio.sleep(3)
    proxy = get_rpc_proxy(IBench, index)
    await proxy.run_timer(10)


async def qps():
    last = 0
    while True:
        await asyncio.sleep(1.0)
        v = finished
        if v - last > 0:
            logger.info("QPS:%d" % (v - last))
            last = v


PORT = 15555


placement = SelfHostedPlacement(PORT)
set_placement_impl(placement)
logger.info(get_placement_impl())


koala_host.init_server(globals())
koala_host.listen_rpc(PORT)
koala_host.create_task(service_1())

for item in range(16):
    i = item
    koala_host.create_task(bench(i))

koala_host.create_task(run_timer(1))
koala_host.create_task(qps())
koala_host.run_server()
