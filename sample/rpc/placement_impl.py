import asyncio
import time
import weakref
from koala.membership.server_node import ServerNode
from koala.placement.placement import Placement
from koala.network.socket_session import SocketSessionManager
from koala.membership.server_node import ServerNodeMetaData
from koala.network.constant import CODEC_RPC
from koala.membership.membership_manager import MembershipManager
from koala.message.message import HeartBeatRequest


_membership = MembershipManager()
_session_manager = SocketSessionManager()


class RpcSelfPlacement(Placement):
    def __init__(self, port: int, service_list: [str]):
        super().__init__()
        self.server_port = "%d" % port
        self.proxy = None

        self.server_node = ServerNodeMetaData()
        self.server_node.server_uid = 1
        self.server_node.host = "127.0.0.1"
        self.server_node.port = self.server_port
        self.server_node.service_type = service_list
        self.server_node.server_name = "sample_self_rpc_0"
        self.server_node.heartbeat_time = int(time.time())

        pass

    def server_id(self) -> int:
        return self.server_node.server_uid
        pass

    def register_server(self):
        pass

    def set_load(self, load: int):
        pass

    def _on_remove_server(self, node: ServerNode):
        pass

    async def placement_loop(self):
        await asyncio.sleep(1.0)
        self.server_node.heartbeat_time = int(time.time())
        if self.proxy is None or self.proxy() is None:
            self.add_server(self.server_node)
        if int(time.time()) % 5 == 0:
            if self.proxy is not None and self.proxy() is not None:
                heartbeat = HeartBeatRequest()
                heartbeat.milli_seconds = int(time.time() * 1000)
                self.proxy().send_message(heartbeat)
        pass

    def _on_add_server(self, node: ServerNode):
        proxy = _session_manager.connect(node.host, node.port, CODEC_RPC)
        self.proxy = weakref.ref(proxy)
        node.set_session(proxy)
        pass

    def find_position_in_cache(self, i_type: str, uid: object) -> ServerNode:
        return _membership.get_member(self.server_node.server_uid)
        pass

    def find_position(self, i_type: str, uid: object) -> ServerNode:
        return _membership.get_member(self.server_node.server_uid)
        pass

    def remove_position_cache(self, i_type: str, uid: object):
        pass


