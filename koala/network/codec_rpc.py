import pickle
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *


KOLA_MAGIC = "KOLA".encode()


# 4字节magic `KOLA`
# 4字节小段长度
# N字节包体

class CodecRpc(Codec):

    def __init__(self):
        super(CodecRpc, self).__init__(CODEC_RPC)

    def decode(self, buffer: Buffer):
        # TODO
        # 这边需要对包的长度进行判断
        magic = buffer.read(4).decode()
        if magic != "KOLA":
            raise Exception("header exception, magic number not correct")
        body_length = int.from_bytes(buffer.read(4), 'little')
        body = buffer.read(body_length)
        return pickle.loads(body)

    def encode(self, msg: object) -> bytes:
        data = pickle.dumps(msg, pickle.HIGHEST_PROTOCOL)
        body_length = int(len(data)).to_bytes(4, 'little')
        return b"".join((KOLA_MAGIC, body_length, data))
