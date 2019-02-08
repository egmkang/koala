from sample.player import *
import gevent
from rpc.rpc_proxy import RpcProxyObject

s = "fdsljflkdsfjh;lsdahgds;ghfd;lgkj;fdlkgjs'gjf"

Counter = 1

def bench():
    proxy = RpcProxyObject(TestPlayer, RPC_ENTITY_TYPE_PLAYER, random.randint(1, 100), RpcContext.GetEmpty())
    while True:
        try:
            proxy.say(s[0: random.randint(1, len(s))])
        except Exception as e:
            print(e)
        global Counter
        Counter += 1

def print_counter():
    while True:
        gevent.sleep(1)
        global Counter
        c = Counter
        print("%sw/s" % (c / 10000))
        Counter -= c


gevent.spawn(lambda: print_counter())

for x in range(32):
    gevent.spawn(lambda: bench())

if __name__ == "__main__":
    server = RpcServer(1002)
    server.run()
