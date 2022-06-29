from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *
from koala.message import *
from koala.message.rpc_message import RpcMessage
from koala.message.base import find_model, JsonMessage
from koala.logger import logger
from koala.utils import json_loads, json_dumps, orjson_dumps


KOLA_MAGIC = "KOLA".encode()
meta_name_length_bytes = bytearray(b"0")

# 4字节magic `KOLA`
# 4字节小端Meta
# 4字节小端Body
# N字节Meta
# M字节Body


class CodecRpc(Codec):
    HEADER_LENGTH = 12
    CLASS_NAME_CACHE: Dict[Type[JsonMessage], bytes] = {}

    def __init__(self):
        super(CodecRpc, self).__init__(CODEC_RPC)

    @classmethod
    def _encode_meta(cls, o: JsonMessage) -> bytes:
        # 1字节长度
        # N字节MessageName
        # M字节json
        _class = o.__class__
        name_bytes = cls.CLASS_NAME_CACHE.get(_class, None)
        if not name_bytes:
            if _class not in cls.CLASS_NAME_CACHE:
                name: str = _class.__qualname__
                cls.CLASS_NAME_CACHE[_class] = name.encode()
            name_bytes = cls.CLASS_NAME_CACHE[_class]
        json_data: bytes = (
            cast(bytes, json_dumps(o.to_dict()))
            if not orjson_dumps
            else orjson_dumps(o)
        )
        global meta_name_length_bytes
        meta_name_length_bytes[0] = len(name_bytes)
        return b"".join((meta_name_length_bytes, name_bytes, json_data))

    @classmethod
    def _decode_meta(cls, array: bytearray) -> Optional[JsonMessage]:
        name_length = array[0]
        name = bytes(array[1 : name_length + 1])
        model = find_model(name)
        if model is not None:
            json = json_loads(array[name_length + 1 :])
            return model.from_dict(json)
        return None

    def decode(self, buffer: Buffer) -> Optional[RpcMessage]:
        if buffer.readable_length() < self.HEADER_LENGTH:
            return None
        # 这边需要对包的长度进行判断
        header = buffer.slice(self.HEADER_LENGTH)
        magic = str(header[:4], "utf-8")
        meta_length = int.from_bytes(header[4:8], "little")
        body_length = int.from_bytes(header[8:], "little")
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
        if not isinstance(msg, RpcMessage):
            msg = RpcMessage.from_msg(cast(JsonMessage, msg))
        msg = cast(RpcMessage, msg)
        if msg is None:
            raise Exception("send a None msg")
        meta_data = self._encode_meta(msg.meta)
        # body直接就是bytes
        # 参数的序列化需要放到rpc call的地方
        # gateway也可以用这个协议来做非RPC协议的传输
        body_data = msg.body if msg.body else b""
        return b"".join(
            (
                KOLA_MAGIC,
                int(len(meta_data)).to_bytes(4, "little"),
                int(len(body_data)).to_bytes(4, "little"),
                meta_data,
                body_data,
            )
        )
