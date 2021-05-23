from typing import Dict
from koala.singleton import Singleton
from .server_node import ServerNode


@Singleton
class MembershipManager(object):
    def __init__(self):
        self.__dict: Dict[int, ServerNode] = dict()
        pass

    def get_member(self, server_uid: int) -> ServerNode:
        if server_uid in self.__dict:
            return self.__dict[server_uid]

    def add_member(self, member: ServerNode):
        self.__dict[member.server_uid] = member

    def remove_member(self, server_uid: int):
        if server_uid in self.__dict:
            del self.__dict[server_uid]

