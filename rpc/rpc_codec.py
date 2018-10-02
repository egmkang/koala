import pickle
from .rpc_constant import *
from utils.id_gen import IdGenerator

_global_id_generator: IdGenerator = None

def InitIDGenerator(server_id):
    global _global_id_generator
    _global_id_generator = IdGenerator(server_id)

class RpcRequest:
    def __init__(self):
        self.clear()

    def clear(self):
        self.host = ""
        if _global_id_generator != None:
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


def CodecEncode(obj):
    data = pickle.dumps(obj, pickle.HIGHEST_PROTOCOL)
    length = int(len(data)).to_bytes(RPC_HEADER_LEN, 'little')
    return length + data

def CodecDecode(data:bytes):
    obj = pickle.loads(data)
    return obj


def test_rpc_request_encode():
    obj = RpcRequest()
    obj.host = "1212"
    obj.entity_id = 1
    obj.method = "f"
    obj.entity_type = 1
    obj.request_id = 232323
    obj.args = (1, "1212")

    data = CodecEncode(obj)
    print(data)


#test_rpc_request_encode()