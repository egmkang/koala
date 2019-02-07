from datetime import datetime
from abc import ABCMeta, abstractmethod
from utils.log import logger
from rpc.rpc_proxy import RpcProxyObject
from gevent.queue import Queue


_empty_context = None

class RpcContext(object):
    def __init__(self):
        self.host = ""
        self.request_id = 0
        self.queue = Queue()
        self.running = False

    def SendMessage(self, obj):
        self.queue.put(obj)


    @staticmethod
    def GetEmpty():
        global _empty_context
        if _empty_context is None:
            _empty_context = RpcContext()
            _empty_context.host = None
            _empty_context.request_id = None
        return _empty_context


class Entity(object):
    __metaclass__ = ABCMeta

    def __init__(self, entity_type, uid:int):
        self._uid = uid
        self._entity_type = entity_type
        self._create_time = datetime.now()
        self._context = RpcContext()

        self._rpc_proxy_object_cache = dict()
        logger.info("create entity:(%d,%d)" % (entity_type, uid))

    def __del__(self):
        logger.info("delete entity:(%d,%d)" % (self._entity_type, self._uid))

    def get_entity_type(self):
        return self._entity_type

    def get_uid(self):
        return self._uid

    def get_create_time(self):
        return self._create_time

    def context(self) -> RpcContext:
        return self._context

    #获取远程对象的代理
    def get_object_proxy(self, cls, _type, _uid):
        if (_type, _uid) not in self._rpc_proxy_object_cache:
            self._rpc_proxy_object_cache[(_type, _uid)] = RpcProxyObject(cls, _type, _uid, self.context())
        return self._rpc_proxy_object_cache[(_type, _uid)]

    @abstractmethod
    def load_from_db(self):
        pass