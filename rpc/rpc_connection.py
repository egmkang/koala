import asyncio
from utils.buffer import Buffer
from .rpc_codec import *
from .rpc_future import *
from utils.log import logger

_session_id = 0

class RpcConnection:
    def __init__(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
        self.reader = reader
        self.writer = writer
        self.address = "%s:%s" % writer.get_extra_info("peername")
        self.buffer = Buffer()
        self.stop_ = False


    def close(self):
        logger.info("close rpc connection %s" % (self.address))
        self.writer.close()
        self.stop_ = True


    async def recv_message(self):
        while not self.stop_:
            data = await self._recv_data()
            obj = CodecDecode(data)
            logger.debug("rpc recv %s, %s, Ip:%s" % (obj.__class__.__name__, obj.request_id, self.address))
            if isinstance(obj, RpcRequest):
                return obj
            else:
                self._dispatch_response(obj)

    def _dispatch_response(self, resp: RpcResponse):
        future: asyncio.Future = GetFuture(resp.request_id)
        if future == None:
            logger.error("dispatch rpc response: %s, future not found" % (resp.request_id))
            return
        future.set_result(resp)

    def _try_decode(self):
        readable_length = self.buffer.readable_length()
        if readable_length <= RPC_HEADER_LEN:
            return None
        need_length = int.from_bytes(self.buffer.slice(RPC_HEADER_LEN), 'little') + RPC_HEADER_LEN
        if need_length > readable_length:
            return None
        data = self.buffer.slice(need_length)[RPC_HEADER_LEN:]
        self.buffer.has_read(need_length)
        return data

    async def _recv_data(self):
        while not self.stop_:
            data = self._try_decode()
            if data is not None:
                return data
            self.buffer.shrink()

            data = await self.reader.read(1024)
            if data == None or len(data) == 0:
                return None
            self.buffer.append(data)


    async def send_message(self, obj):
        logger.debug("rpc send %s, %s, Ip:%s" % (obj.__class__.__name__, obj.request_id, self.address))
        data = CodecEncode(obj)
        await self._send_data(data)


    async def _send_data(self, data: bytes):
        self.writer.write(data)
        #await self.writer.drain()