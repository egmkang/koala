from sample.player import *

s = "fdsljflkdsfjh;lsdahgds;ghfd;lgkj;fdlkgjs'gjf"

Counter = 1

async def bench():
    proxy = RpcProxyObject(TestPlayer, ENTITY_TYPE_PLAYER, random.randint(1, 100), RpcContext.GetEmpty())
    while True:
        try:
            await proxy.say(s[0: random.randint(1, len(s))])
        except Exception as e:
            print(e)
        global Counter
        Counter += 1

async def print_counter():
    while True:
        await asyncio.sleep(1)
        global Counter
        c = Counter
        print("%sw/s" % (c / 10000))
        Counter -= c

server = RpcServer(1002)

server.create_task(print_counter())

for x in  range(32):
    server.create_task(bench())

server.run()
