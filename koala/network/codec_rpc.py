import pickle
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *
from koala.message import *
from koala.message.util import find_model


KOLA_MAGIC = "KOLA".encode()


Message = Tuple[BaseModel, bytes]


# 4字节magic `KOLA`
# 4字节小端Meta
# 4字节小端Body
# N字节Meta
# M字节Body
class CodecRpc(Codec):
    HEADER_LENGTH = 12

    def __init__(self):
        super(CodecRpc, self).__init__(CODEC_RPC)

    @classmethod
    def _encode_meta(cls, o: BaseModel) -> bytes:
        # 1字节长度
        # N字节MessageName
        # M字节json
        name: str = o.__class__.__qualname__
        return b"".join((int.to_bytes(len(name), 1, 'little'), name.encode(), o.json().encode()))

    @classmethod
    def _decode_meta(cls, array: bytes) -> Optional[BaseModel]:
        name_length = array[0]
        name = array[1: name_length + 1].decode()
        model = find_model(name)
        if model is not None:
            return model.parse_raw(array[name_length + 1:])
        return None

    def decode(self, buffer: Buffer) -> Optional[Message]:
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
            return meta, body_data if body_data else b""
        raise Exception("decode meta fail")

    def encode(self, msg: object) -> bytes:
        assert isinstance(msg, tuple) and len(msg) == 2
        meta, body = cast(Message, msg)
        meta_data = self._encode_meta(meta)
        # body直接就是bytes
        # 参数的序列化需要放到rpc call的地方
        # gateway也可以用这个协议来做非RPC协议的传输
        body_data = body if body else b""
        return b"".join((KOLA_MAGIC,
                         int(len(meta_data)).to_bytes(4, 'little'),
                         int(len(body_data)).to_bytes(4, 'little'),
                         meta_data,
                         body_data))
