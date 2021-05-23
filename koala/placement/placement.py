import traceback
from abc import ABC, abstractmethod
from koala.typing import *
from koala.membership.server_node import ServerNode, ServerNodeMetaData
from koala.membership.membership_manager import MembershipManager
from koala.singleton import Singleton
from koala.logger import logger


_membership_manager = MembershipManager()


class Placement(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def server_id(self) -> int:
        pass

    @abstractmethod
    def register_server(self):
        pass

    @abstractmethod
    def set_load(self, load: int):
        pass

    @abstractmethod
    def find_position_in_cache(self, i_type: str, uid: object) -> ServerNode:
        pass

    @abstractmethod
    async def find_position(self, i_type: str, uid: object) -> ServerNode:
        pass

    @abstractmethod
    def remove_position_cache(self, i_type: str, uid: object):
        pass

    def add_server(self, node: ServerNodeMetaData):
        server = ServerNode(node)
        _membership_manager.add_member(server)
        try:
            self._on_add_server(server)
            logger.info("PD AddServer, ServerID:%d, Address:%s:%s" % (server.server_uid, server.host, server.port))
        except:
            logger.error("Placement.AddServer, ServerUID:%d, Exception:%s" % (node.server_uid, traceback.format_exc()))
            pass

    def remove_server(self, node: ServerNode):
        _membership_manager.remove_member(node.server_uid)
        try:
            self._on_remove_server(node)
            logger.info("PD RemoveServer, ServerID:%d, Address:%s:%s" % (node.server_uid, node.host, node.port))
        except:
            logger.error("Placement.RemoveServer, ServerUID:%d, Exception:%s" %
                         (node.server_uid, traceback.format_exc()))
            pass

    """该函数需要去主动连接服务器, 然后将proxy和服务器关联上, 连接断开的话, 也需要去重试
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


@Singleton
class PlacementInjection(object):
    def __init__(self):
        self.__impl: Optional[Placement, None] = None
        pass

    def set_impl(self, impl: Placement):
        self.__impl = impl

    @property
    def impl(self) -> Placement:
        return self.__impl
