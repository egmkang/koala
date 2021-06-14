import json
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *
from koala.message import *
from koala.message.rpc_message import RpcMessage
from koala.message.base import find_model, JsonMessage
from koala.logger import logger

KOLA_MAGIC = "KOLA".encode()
json_dumps = lambda o: json.dumps(o).encode()
json_loads = lambda b: json.loads(b.decode())


# 4字节magic `KOLA`
# 4字节小端Meta
# 4字节小端Body
# N字节Meta
# M字节Body
class CodecRpc(Codec):
    HEADER_LENGTH = 12

    def __init__(self):
        super(CodecRpc, self).__init__(CODEC_RPC)
        try:
            pass
            global json_loads, json_dumps
            import orjson
            json_loads = orjson.loads
            json_dumps = orjson.dumps
        except:
            pass

    @classmethod
    def _encode_meta(cls, o: JsonMessage) -> bytes:
        # 1字节长度
        # N字节MessageName
        # M字节json
        global json_dumps
        name: str = o.__class__.__qualname__
        json_data: bytes = cast(bytes, json_dumps(o.to_dict()))
        return b"".join((int.to_bytes(len(name), 1, 'little'), name.encode(), json_data))

    @classmethod
    def _decode_meta(cls, array: bytes) -> Optional[JsonMessage]:
        global json_loads
        name_length = array[0]
        name = array[1: name_length + 1].decode()
        model = find_model(name)
        if model is not None:
            json = json_loads(array[name_length + 1:])
            return model.from_dict(json)
        return None

    def decode(self, buffer: Buffer) -> Optional[RpcMessage]:
        if buffer.readable_length() < self.HEADER_LENGTH:
            return None
        # 这边需要对包的长度进行判断
        header = buffer.slice(self.HEADER_LENGTH)
        magic = header[:4].decode()
        meta_length = int.from_bytes(header[4:8], 'little')
        body_length = int.from_bytes(header[8:], 'little')
        if buffer.readable_length() < meta_length + body_length + self.HEADER_LENGTH:
            return None
        if magic != "KOLA":
            raise Exception("header exception, magic number not correct")
        buffer.has_read(self.HEADER_LENGTH)
        meta_data = buffer.read(meta_length)
        body_data = buffer.read(body_length)
        meta = self._decode_meta(meta_data)
        if meta is not None:
            return RpcMessage.from_msg(meta, body_data if body_data else b"")
        raise Exception("decode meta fail")

    def encode(self, msg: object) -> bytes:
        if not(hasattr(msg, 'meta') and hasattr(msg, 'body')):
            msg = RpcMessage.from_msg(cast(JsonMessage, msg), None)
        msg = cast(RpcMessage, msg)
        if msg is None:
            raise Exception("send a None msg")
        meta_data = self._encode_meta(msg.meta)
        # body直接就是bytes
        # 参数的序列化需要放到rpc call的地方
        # gateway也可以用这个协议来做非RPC协议的传输
        body_data = msg.body if msg.body else b""
        return b"".join((KOLA_MAGIC,
                         int(len(meta_data)).to_bytes(4, 'little'),
                         int(len(body_data)).to_bytes(4, 'little'),
                         meta_data,
                         body_data))
