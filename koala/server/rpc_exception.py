RPC_ERROR_BEGIN = 10000
RPC_ERROR_INTERFACE_INVALID = RPC_ERROR_BEGIN + 1
RPC_ERROR_IMPL_INVALID = RPC_ERROR_BEGIN + 2
RPC_ERROR_UNKNOWN = RPC_ERROR_BEGIN + 3
RPC_ERROR_ENTITY_NOT_FOUND = RPC_ERROR_BEGIN + 4
RPC_ERROR_METHOD_NOT_FOUND = RPC_ERROR_BEGIN + 5
RPC_ERROR_POSITION_CHANGED = RPC_ERROR_BEGIN + 6


class RpcException(Exception):
    def __init__(self, code: int, msg: str):
        self.code = 0
        self.msg = ""

    @staticmethod
    def interface_invalid():
        return RpcException(RPC_ERROR_INTERFACE_INVALID, "interface invalid")

    @staticmethod
    def impl_invalid():
        return RpcException(RPC_ERROR_IMPL_INVALID, "impl invalid")

    @staticmethod
    def entity_not_found():
        return RpcException(RPC_ERROR_ENTITY_NOT_FOUND, "entity not found")

    @staticmethod
    def method_not_found():
        return RpcException(RPC_ERROR_METHOD_NOT_FOUND, "method not found")

    @staticmethod
    def position_changed():
        return RpcException(RPC_ERROR_POSITION_CHANGED, "position changed")
