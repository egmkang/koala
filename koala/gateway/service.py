from abc import ABC
from koala.meta.rpc_meta import *


@rpc_interface
class IGateway(ABC):
    def __init__(self):
        pass


@rpc_impl(IGateway)
class GatewayImpl(IGateway):
    def __init__(self):
        super().__init__()
        pass


