from koala.koala_typing import *
from koala.singleton import Singleton
from koala.membership.server_node import ServerNode


class MembershipManager(Singleton):
    def __init__(self):
        super(MembershipManager, self).__init__()
        self.__dict: Dict[int, ServerNode] = dict()
        pass

    def get_member(self, server_uid: int) -> Optional[ServerNode]:
        if server_uid in self.__dict:
            return self.__dict[server_uid]
        return None

    def get_members(self) -> Dict[int, ServerNode]:
        return dict(self.__dict)

    def add_member(self, member: ServerNode):
        self.__dict[member.server_uid] = member

    def remove_member(self, server_uid: int):
        if server_uid in self.__dict:
            del self.__dict[server_uid]
