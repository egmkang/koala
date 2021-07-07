import asyncio
import random
from koala.server import server_base
from koala.server.actor_base import ActorBase
from koala.meta.rpc_meta import *
from koala.network.constant import CODEC_RPC
from koala.network.socket_session import SocketSessionManager
from koala.placement.placement import get_placement_impl, set_placement_impl
from koala.pd.simple import SelfHostedPlacement
from koala.server.rpc_proxy import get_rpc_proxy
from koala.server.actor_timer import ActorTimer
from koala.logger import logger


@rpc_interface
class IService1:
    async def say_hello(self, hello: str) -> str:
        pass

    async def say(self):
        pass

    async def reentrancy(self) -> object:
        pass


@rpc_interface
class IService2:
    async def hello(self, my_id: object, times: int) -> str:
        pass


@rpc_impl(IService1)
class Service1Impl(IService1, ActorBase):
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
class IBench:
    async def echo(self, e: str) -> str:
        pass

    async def run_timer(self, count: int):
        pass


@rpc_impl(IBench)
class BenchImpl(IBench, ActorBase):
    def __init__(self):
        super(BenchImpl, self).__init__()

    async def echo(self, e: str) -> str:
        return e

    async def run_timer(self, count: int):
        weak_actor = self.weak

        def f(timer: ActorTimer):
            logger.info("timer, tick:%s" % timer.tick_count)
            if timer.tick_count >= count:
                a = weak_actor()
                a.unregister_timer(timer.timer_id)
        self.register_timer(1000, f)


finished = 0


async def bench(index: object):
    global finished
    await asyncio.sleep(3)
    proxy = get_rpc_proxy(IBench, index)
    while True:
        _ = await proxy.echo("12121212")
        finished += 1


async def run_timer(index: object):
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


placement = SelfHostedPlacement(15555)
set_placement_impl(placement)
logger.info(get_placement_impl())


server_base.init_server()
server_base.listen(15555, CODEC_RPC)
server_base.create_task(service_1())

# for item in range(16):
#     i = item
#     server_base.create_task(bench(i))

server_base.create_task(run_timer(1))
server_base.create_task(qps())

server_base.run_server()
