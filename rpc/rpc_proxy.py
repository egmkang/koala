import time
from .rpc_client import *
from utils.log import logger
from utils.cls_method_cache import ClassMethodCache, MethodNotFoundException
from entity.entity import ActorContext
from entity.proxy_factory import proxy_object_type

_cls_method_cache = ClassMethodCache()


class RpcMethodNotFound(Exception):
    pass


class RpcPositionNotFound(Exception):
    pass


class RpcSocketError(Exception):
    pass


class RpcProxyMethod:
    def __init__(self, entity_type, entity_id, method_name, context: ActorContext):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.method_name = method_name
        self.context = context

        if self.context is None:
            self.context = ActorContext.empty()

        from cluster.entity_position import EntityPositionCache
        from .rpc_server import RpcServer

        self.server = RpcServer(-1)
        self.position_cache = EntityPositionCache()
        self.client: RpcClient = None
        pass

    def _find_client(self):
        pos = self.position_cache.find_entity_pos(self.entity_type, self.entity_id)
        if pos is None:
            raise RpcPositionNotFound()
        self.client = self.server.rpc_connect(pos.address[0], pos.address[1])

    def __call__(self, *args, **kwargs):
        if self.client is None:
            self._find_client()
        if self.client is not None:
            logger.debug("send request, %s" % (self.method_name))
            return self.client.send_request(self.context.host, self.context.request_id,
                                                  self.entity_type, self.entity_id, self.method_name, *args, **kwargs)
        else:
            raise RpcPositionNotFound()


@proxy_object_type
class RpcProxyObject:
    def __init__(self, cls, _type, uid, context: ActorContext):
        self.entity_type = _type
        self.entity_id = uid
        self.cls = cls
        self.last_call_time = time.time()
        self.method_set = _cls_method_cache.get_cls_method_set(cls)
        self.context = context

        self.method_cache = dict()
        pass

    def __getattr__(self, name):
        if name not in self.method_set:
            raise MethodNotFoundException()
        if name not in self.method_cache:
            method: RpcProxyMethod = RpcProxyMethod(self.entity_type, self.entity_id, name, self.context)
            self.method_cache[name] = method
        self.last_call_time = time.time()
        return self.method_cache[name]

