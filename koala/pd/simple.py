import asyncio
import time
from koala.koala_typing import *
from koala.membership.server_node import ServerNode
from koala.placement.placement import Placement
from koala.network.socket_session import SocketSessionManager, SocketSession
from koala.network.tcp_session import TcpSocketSession
from koala.network.constant import CODEC_RPC
from koala.membership.membership_manager import MembershipManager
from koala.message import RequestHeartBeat
from koala.server import rpc_meta
from koala.logger import logger


_membership = MembershipManager()
_session_manager = SocketSessionManager()


class SelfHostedPlacement(Placement):
    def __init__(self, port: int):
        super(SelfHostedPlacement, self).__init__()
        self.server_port = "%d" % port
        self.session: Optional[SocketSession] = None
        self.server_node: Optional[ServerNode] = None
        pass

    def _init_server_node(self):
        if not self.server_node:
            service_list = rpc_meta.get_all_services()
            self.server_node = ServerNode(
                server_uid=1,
                host="127.0.0.1",
                port=self.server_port,
                service_type=service_list,
                server_name="single node cluster",
            )

    def server_id(self) -> int:
        self._init_server_node()
        assert self.server_node
        return self.server_node.server_uid

    async def register_server(self):
        pass

    def get_all_servers(self) -> List[ServerNode]:
        self._init_server_node()
        assert self.server_node
        return [self.server_node]

    def set_load(self, load: int):
        pass

    def _on_remove_server(self, node: ServerNode):
        pass

    async def placement_loop(self):
        await asyncio.sleep(1.0)
        self._init_server_node()
        assert self.server_node
        if self.session is None:
            self.add_server(self.server_node)
        if int(time.time()) % 5 == 0:
            if self.session is not None:
                heartbeat = RequestHeartBeat()
                heartbeat.milli_seconds = int(time.time() * 1000)
                await self.session.send_message(heartbeat)
        pass

    def _on_add_server(self, node: ServerNode):
        asyncio.create_task(self._try_connect(node))
        pass

    async def delete_server(self, server_id: int):
        pass

    def find_position_in_cache(self, i_type: str, uid: object) -> Optional[ServerNode]:
        self._init_server_node()
        assert self.server_node
        return _membership.get_member(self.server_node.server_uid)
        pass

    async def find_position(self, i_type: str, uid: object) -> Optional[ServerNode]:
        self._init_server_node()
        assert self.server_node
        return _membership.get_member(self.server_node.server_uid)

    def remove_position_cache(self, i_type: str, uid: object):
        pass

    async def _try_connect(self, node: ServerNode):
        try:
            session = await TcpSocketSession.connect(
                node.host, int(node.port), CODEC_RPC
            )
            if session is not None:
                node.set_session(session)
                logger.info(
                    "try_connect ServerID:%d, Host:%s:%s success"
                    % (node.server_uid, node.host, node.port)
                )
                self.session = session
        except Exception as e:
            logger.error(
                "try_connect ServerID:%d, Host:%s:%s, Exception:%s"
                % (node.server_uid, node.host, node.port, e)
            )
        pass
