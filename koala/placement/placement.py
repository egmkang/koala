import traceback
from abc import ABC, abstractmethod
from koala.typing import *
from koala.membership.server_node import ServerNode
from koala.membership.membership_manager import MembershipManager
from koala.singleton import Singleton
from koala.logger import logger


_membership_manager = MembershipManager()


class Placement(ABC):
    __placement_impl: Optional["Placement"] = None

    @abstractmethod
    def server_id(self) -> int:
        pass

    @abstractmethod
    async def register_server(self):
        pass

    @abstractmethod
    async def delete_server(self, server_id: int):
        pass

    @abstractmethod
    def set_load(self, load: int):
        pass

    @abstractmethod
    def find_position_in_cache(self, i_type: str, uid: object) -> Optional[ServerNode]:
        pass

    @abstractmethod
    async def find_position(self, i_type: str, uid: object) -> Optional[ServerNode]:
        pass

    @abstractmethod
    def remove_position_cache(self, i_type: str, uid: object):
        pass

    def add_server(self, node: ServerNode):
        server = node
        _membership_manager.add_member(server)
        try:
            self._on_add_server(server)
            logger.info("PD AddServer, ServerID:%d, Address:%s:%s, Desc:%s" %
                        (server.server_uid, server.host, server.port, server.desc))
        except Exception as e:
            logger.error("Placement.AddServer, ServerUID:%d, Exception:%s, StackTrace:%s" %
                         (node.server_uid, e, traceback.format_exc()))
            pass

    def remove_server(self, node: ServerNode):
        _membership_manager.remove_member(node.server_uid)
        try:
            self._on_remove_server(node)
            logger.info("PD RemoveServer, ServerID:%d, Address:%s:%s" %
                        (node.server_uid, node.host, node.port))
        except Exception as e:
            logger.error("Placement.RemoveServer, ServerUID:%d, Exception:%s, StackTrace:%s" %
                         (node.server_uid, e, traceback.format_exc()))
            pass

    """该函数需要去主动连接服务器, 然后将session和服务器关联上, 连接断开的话, 也需要去重试
    """
    @abstractmethod
    def _on_add_server(self, node: ServerNode):
        pass

    """该函数需要把已经存在的连接关闭掉, 正在尝试的连接也停掉(包括重试)
    """
    @abstractmethod
    def _on_remove_server(self, node: ServerNode):
        pass

    """服务器启动需要开启一个协程去执行placement_loop, 去维护集群的元数据信息
       该loop充当客户端的角色, 还需要有一个服务器来保存和维护元数据信息
    """
    @abstractmethod
    async def placement_loop(self):
        pass

    @classmethod
    def instance(cls) -> 'Placement':
        assert cls.__placement_impl
        return cls.__placement_impl

    @classmethod
    def set_instance(cls, impl: "Placement"):
        cls.__placement_impl = impl
        logger.info("init placement impl %s" % cls.__placement_impl)
