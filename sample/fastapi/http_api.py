from koala.server.fastapi import *
from koala.server import rpc_proxy
from sample.interfaces import IPlayer


@app.get("/")
def root():
    return "hello world"


@app.get("/echo/{msg}")
async def echo(msg: str):
    proxy = rpc_proxy.get_rpc_proxy(IPlayer, "1")
    result = await proxy.echo(msg)
    return result
