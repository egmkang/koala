import pickle
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *


KOLA_MAGIC = "KOLA".encode()


# 4字节magic `KOLA`
# 4字节小段长度
# N字节包体

class CodecRpc(Codec):
    HEADER_LENGTH = 8

    def __init__(self):
        super(CodecRpc, self).__init__(CODEC_RPC)

    def decode(self, buffer: Buffer):
        if buffer.readable_length() < self.HEADER_LENGTH:
            return None
        # 这边需要对包的长度进行判断
        header = buffer.slice(self.HEADER_LENGTH)
        magic = header[:4].decode()
        body_length = int.from_bytes(header[4:], 'little')
        if buffer.readable_length() < body_length + self.HEADER_LENGTH:
            return None
        buffer.has_read(self.HEADER_LENGTH)
        if magic != "KOLA":
            raise Exception("header exception, magic number not correct")
        body = buffer.read(body_length)
        return pickle.loads(body)

    def encode(self, msg: object) -> bytes:
        data = pickle.dumps(msg, pickle.HIGHEST_PROTOCOL)
        body_length = int(len(data)).to_bytes(4, 'little')
        return b"".join((KOLA_MAGIC, body_length, data))
