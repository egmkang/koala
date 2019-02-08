import pickle
from .rpc_constant import *
from utils.id_gen import IdGenerator
from net.codec import Codec
from utils.buffer import Buffer

_global_id_generator: IdGenerator = None


def InitIDGenerator(server_id):
    global _global_id_generator
    _global_id_generator = IdGenerator(server_id)


class RpcRequest:
    def __init__(self):
        self.clear()

    def clear(self):
        self.host = ""
        if _global_id_generator is not None:
            self.request_id = _global_id_generator.NextId()
        else:
            self.request_id = 0
        self.entity_type = 0
        self.entity_id = 0
        self.method = ""
        self.args = ()
        self.kwargs = dict()


class RpcResponse:
    def __init__(self):
        self.clear()

    def clear(self):
        self.request_id = 0
        self.error_code = 0
        self.method = ""
        self.error = ""
        self.response = []


def codec_encode(obj):
    data = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    length = int(len(data)).to_bytes(RPC_HEADER_LEN, 'little')
    return length + data


def codec_decode(data: bytes):
    obj = pickle.loads(data)
    return obj


class RpcCodec(Codec):
    def __init__(self):
        super().__init__()
        pass

    # (buffer, conn) => object
    def decode(self, buffer: Buffer, conn):
        readable_length = buffer.readable_length()
        if readable_length <= RPC_HEADER_LEN:
            return None
        need_length = int.from_bytes(buffer.slice(RPC_HEADER_LEN), 'little') + RPC_HEADER_LEN
        if need_length > readable_length:
            return None
        data = buffer.slice(need_length)[RPC_HEADER_LEN:]
        buffer.has_read(need_length)
        return codec_decode(data)

    # (msg, conn) => bytes
    def encode(self, msg, conn) -> bytes:
        return codec_encode(msg)


def test_rpc_request_encode():
    obj = RpcRequest()
    obj.host = "1212"
    obj.entity_id = 1
    obj.method = "f"
    obj.entity_type = 1
    obj.request_id = 232323
    obj.args = (1, "1212")

    data = codec_encode(obj)
    print(data)


if __name__ == "__main__":
    test_rpc_request_encode()
