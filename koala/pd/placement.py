import asyncio
import pylru
import time
from koala.typing import *
from koala.placement.placement import Placement
from koala.membership.server_node import ServerNode
from koala.membership.server_node import ServerNodeMetaData
from koala.membership.membership_manager import MembershipManager
from koala.network.constant import CODEC_RPC
from koala.message.message import HeartBeatRequest
from koala.network.socket_session import SocketSessionManager
from koala.pd import api
from koala.conf.config import Config
from koala.error.error_code import *
from koala.logger import logger


PLACEMENT_CACHE_SIZE = 10 * 10000

_config = Config()
_membership = MembershipManager()
_proxy_manager = SocketSessionManager()


class PDPlacementImpl(Placement):
    def __init__(self):
        super().__init__()
        self._lease_id = 0
        self._server_id = 0
        self._load = 0
        self._last_heart_beat = time.time()
        self._recent_removed: Set[int] = set()
        self._recent_added: Set[int] = set()
        self._lru_cache = pylru.lrucache(PLACEMENT_CACHE_SIZE)
        pass

    def server_id(self) -> int:
        return self._server_id

    def register_server(self):
        resp = api.new_server_id()
        if resp.error_code == 0:
            self._server_id = resp.id
            logger.info("PD Register Server Success, ServerID:%d" % self._server_id)
        else:
            logger.error("PD Register Server Fail, ExitCode:%d" % ERROR_PD_NEW_SERVER.code)
            exit(ERROR_PD_NEW_SERVER.code)
            return
        resp = api.register_server(self._server_id,
                                   _config.start_time,
                                   _config.ttl,
                                   _config.address,
                                   _config.services,
                                   _config.desc)
        if resp.error_code == 0:
            self._lease_id = resp.lease_id
            logger.info("ServerID:%d, LeaseID:%d" % (self._server_id, self._lease_id))
            l = ["%s => %s" % (k, _config.services[k]) for k in _config.services]
            logger.info("Host Services:%s" % (", ".join(l)))
            asyncio.create_task(self._heart_beat_loop())
        else:
            logger.error("%d, %s" % (ERROR_PD_NEW_SERVER.code, ERROR_PD_NEW_SERVER.message))
            exit(ERROR_PD_REGISTER_SERVER.code)
        pass

    def _pd_keep_alive(self) -> api.KeepAliveServerResponse:
        if time.time() - self._last_heart_beat > _config.ttl:
            logger.error("%s, %s" % (ERROR_PD_KEEP_ALIVE_TIME_OUT.code, ERROR_PD_KEEP_ALIVE_TIME_OUT.message))
            exit(ERROR_PD_KEEP_ALIVE_TIME_OUT.code)
            pass
        resp = api.keep_alive(self._server_id, self._lease_id, self._load)
        if resp.error_code != 0:
            logger.error("%d, %s" % (ERROR_PD_KEEP_ALIVE.code, ERROR_PD_KEEP_ALIVE.message))
            print(resp.error_msg)
            exit(ERROR_PD_KEEP_ALIVE.code)
        self._last_heart_beat = time.time()
        return resp

    def set_load(self, load: int):
        self._load = load
        pass

    def placement_loop(self):
        resp = self._pd_keep_alive()
        hosts = resp.hosts
        events = resp.events
        self._rebuild_recent_removed(events)
        self._compare_membership(hosts)
        gevent.sleep(_config.ttl / 3)
        pass

    def _compare_membership(self, hosts: Dict[int, api.HostNodeInfo]):
        for removed in self._recent_removed:
            node = _membership.get_member(removed)
            if node is not None:
                self.remove_server(node)
        for server_id in hosts:
            node = _membership.get_member(server_id)
            if node is None:
                node = hosts[server_id]
                self.add_server(PDPlacementImpl._build_node_info(node))
        pass

    @staticmethod
    def _build_node_info(info: api.HostNodeInfo) -> ServerNodeMetaData:
        array = info.address.split(":")
        i = ServerNodeMetaData()
        i.server_uid = info.server_id
        i.server_name = ""
        i.host = array[0]
        i.port = array[1]
        i.service_type = info.services
        return i

    def _rebuild_recent_removed(self, events: List[api.HostNodeAddRemoveEvent]):
        self._recent_removed.clear()
        for item in events:
            for i in item.remove:
                self._recent_removed.add(i)
        pass

    def _on_remove_server(self, node: ServerNode):
        self._recent_added.remove(node.server_uid)
        pass

    def _on_add_server(self, node: ServerNode):
        self._recent_added.add(node.server_uid)
        PDPlacementImpl._try_connect(node)
        pass

    def find_position_in_cache(self, i_type: str, uid: object) -> ServerNode:
        v = self._lru_cache.get((i_type, uid))
        if v is not None:
            server_uid: int = v
            node = _membership.get_member(server_uid)
            return node
        pass

    def find_position(self, i_type: str, uid: object) -> ServerNode:
        node = self.find_position_in_cache(i_type, uid)
        if node is not None and node.proxy is not None:
            return node
        resp = api.find_actor_position(i_type, "%s" % uid, 0)
        if resp.error_code != 0:
            raise Exception("%s" % resp.error_msg)
        node = _membership.get_member(resp.server_id)
        if node is not None:
            self._lru_cache[(i_type, uid)] = node.server_uid
            logger.info("FindActorPosition:%s/%s, ServerID:%s, Address:%s:%s" % (i_type, uid, node.server_uid, node.host, node.port))
        else:
            if (i_type, uid) in self._lru_cache:
                del self._lru_cache[(i_type, uid)]
            logger.info("FindActorPosition:%s/%s position not found" % (i_type, uid))
        return node

    def remove_position_cache(self, i_type: str, uid: object):
        node = self.find_position_in_cache(i_type, uid)
        if node is not None:
            del self._lru_cache[(i_type, uid)]
        pass

    def _heart_beat_loop(self):
        while True:
            try:
                gevent.sleep(_config.ttl / 3)
                self._try_send_heart_beat()
            except:
                pass

    def _try_send_heart_beat(self):
        heart_beat = HeartBeatRequest()
        heart_beat.milli_seconds = int(time.time() * 1000)
        for server_id in self._recent_added:
            host = _membership.get_member(server_id)
            if host is None:
                continue
            if host.proxy is None:
                PDPlacementImpl._try_connect(host)
                continue
            proxy = host.proxy
            proxy.send_message(heart_beat)
        pass

    @staticmethod
    def _try_connect(node: ServerNode):
        proxy = _proxy_manager.connect(node.host, node.port, CODEC_RPC)
        node.set_proxy(proxy)
