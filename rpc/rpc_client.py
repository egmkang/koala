from utils.log import logger
import asyncio
from .rpc_connection import RpcConnection
from .rpc_codec import *
from .rpc_future import *
from .rpc_server import GetServerUniqueID

class RpcClient:
    def __init__(self, host, port, loop):
        self._conn = None
        self._host = host
        self._port = port
        self._loop = loop
        self._connecting = False


    async def connect(self):
        if self._conn is not None:
            return
        if not self._connecting:
            self._connecting = True
            logger.info("connect:%s:%s" % (self._host, self._port))
            reader, writer = await asyncio.open_connection(self._host, self._port, loop=self._loop, limit=RPC_WINDOW_SIZE)
            logger.info("connect:%s:%s complete" % (self._host, self._port))
            self._conn = RpcConnection(reader, writer)
            self._loop.create_task(self._recv_message())
            self._connecting = False
        while True:
            await asyncio.sleep(0.1)
            if self._conn is not None:
                return

    async def _recv_message(self):
        try:
            await self._conn.recv_message()
        except Exception as e:
            logger.error("RpcClient.recv_message, Exception:%s" % (e))
            self._conn.close()
            self._conn = None

    async def send_request(self, host, request_id, entity_type, entity_id, method, *args, **kwargs):
        await self.connect()

        request = RpcRequest()
        if host is not None:
            request.host = host
        else:
            request.host = GetServerUniqueID()

        if request_id is not None:
            request.request_id = request_id

        request.entity_type = entity_type
        request.entity_id = entity_id
        request.method = method
        request.args = args
        request.kwargs = kwargs

        await self._conn.send_message(request)
        future = asyncio.Future()
        AddFuture(request, future)
        await asyncio.wait_for(future, 5)
        resp: RpcResponse = future.result()
        return resp.response
