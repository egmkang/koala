from datetime import datetime
from abc import ABCMeta, abstractmethod
from utils.log import logger
from .proxy_factory import new_proxy_object
from .rpc_context import RpcContext


class Entity(object):
    __metaclass__ = ABCMeta

    def __init__(self, entity_type: int, uid: int):
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

    # 获取远程对象的代理
    # 用户需要在这个函数上面封装一层
    def get_object_proxy(self, cls, _type, _uid):
        if (_type, _uid) not in self._rpc_proxy_object_cache:
            self._rpc_proxy_object_cache[(_type, _uid)] = new_proxy_object(cls, _type, _uid, self.context())
        return self._rpc_proxy_object_cache[(_type, _uid)]

    @abstractmethod
    def on_active(self):
        pass

    @abstractmethod
    def on_deactive(self):
        pass