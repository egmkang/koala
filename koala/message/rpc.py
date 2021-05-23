_empty_list = []
_empty_dict = dict()


class RpcRequest(object):
    def __init__(self):
        self.service_name = ""
        self.method_name = ""
        self.actor_id = ""
        self.reentrant_id = 0
        self.request_id = 0
        self.args = _empty_list
        self.kwargs = _empty_dict
        self.server_id = 0      # 目标服务器ID
        pass


class RpcResponse(object):
    def __init__(self):
        self.request_id = 0
        self.error_code = 0
        self.error_str = ""
        self.response = _empty_list
        pass


