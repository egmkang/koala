import time
import random
import gevent
from .etcd_helper import EtcdHelper
from utils.singleton import Singleton
from utils.log import logger
from utils.ujson_codec import *


SYNC_MEMBER_TIME = 5    # 同步membership的时间
SYNC_TIMEOUT = 15       # 超时时间, 超过时间服务器会自动退出
MEMBER_TTL = 15         # member存活的时间
START_TIME = 15         # 刚启动的机器不能加入到集群


class MachineInfo:
    def __init__(self, server_id=None):
        self.unique_id = ""                 #服务器唯一ID
        self.server_id = 0                  #服ID
        self.create_time = int(time.time()) #服务器创建的时间
        self.player_count = 0               #玩家数量
        self.update_time = int(time.time()) #更新的时间
        self.address = None                 #本机Server的IP+Port
        if server_id is not None:
            self.server_id = server_id

@Singleton
class MemberShipManager:
    def __init__(self):
        self._members = dict()

    def get_machine_by_unique_id(self, unique_id) -> MachineInfo:
        if unique_id in self._members:
            return self._members[unique_id]
        return None

    def add_machine(self, info: MachineInfo):
        if info.unique_id not in self._members:
            logger.info("MemberShipManager.add_machine, UniqueID:%s, ServerID:%s, Address:%s, CreateTime:%s" %
                        (info.unique_id, info.server_id, info.address, info.create_time))
        self._members[info.unique_id] = info

    def remove_machine(self, unique_id):
        try:
            info: MachineInfo = self._members[unique_id]
            logger.info("MemberShipManager.remove_machine, UniqueID:%s, ServerID:%s, Address:%s, CreateTime:%s" %
                        (info.unique_id, info.server_id, info.address, info.create_time))
            del self._members[unique_id]
        except Exception as e:
            logger.error("MemberShipManager.remove, UniqueID:%s, exception:%s" % (unique_id, e))
            pass

    def try_remove_machines(self, keys):
        current_keys = set(self._members.keys())
        remove = current_keys - set(keys)
        for unique_id in remove:
            self.remove_machine(unique_id)

    def add_machines(self, infos: [MachineInfo]):
        for info in infos:
            self.add_machine(info)

    def random_machine(self):
        # 这边要把刚加入到集群中时间太短的节点过滤掉
        current_time = int(time.time()) - START_TIME
        machines: [MachineInfo] = list(self._members.values())
        count = [machine.player_count for machine in machines if machine.create_time < current_time]
        max_count = max(count) + 100
        count = [max_count - c for c in count]
        total_count = sum(count)
        rand = random.randint(0, total_count)
        total = 0
        for index in range(len(count)):
            total += count[index]
            if rand <= total:
                return machines[index]


# 机器的信息保存在etcd上
# 路径是/machine/{unique_id}
# 例如服务器的Unique是1, 那么路径就是/machine/1, 内容是MachineInfo序列化好的json字符串

_last_update_time = time.time()


def _check_update_time():
    global _last_update_time
    while True:
        if time.time() - _last_update_time >= SYNC_TIMEOUT:
            logger.error("_check_update_time, last_update_time:%s, current_time:%s" % (_last_update_time, time.time()))
            logger.error("event loop stop")
            return
        gevent.sleep(SYNC_MEMBER_TIME)


player_count = 0


def set_player_count(new_count: int):
    global player_count
    player_count = new_count


def update_machine_member_info(info: MachineInfo, etcd: EtcdHelper):
    global _last_update_time, player_count
    _last_update_time = time.time()
    gevent.spawn(lambda: _check_update_time())

    while True:
        path = "/machine/%s" % info.unique_id
        info.player_count = player_count
        content = CodecUjsonEncode(info).encode()
        try:
            etcd.put(path, content, MEMBER_TTL)
            _last_update_time = time.time()
        except Exception as e:
            logger.error("UpdateMachineMemberInfo, execption:%s" % e)

        gevent.sleep(SYNC_MEMBER_TIME)


def _update_member_ship(member_ship: MemberShipManager, result):
    infos = [CodeUjsonDecode(child[0].decode(), MachineInfo) for child in result]
    keys = [info.unique_id for info in infos]
    member_ship.try_remove_machines(keys)
    member_ship.add_machines(infos)


# 这边没有删除超时的节点
def get_members_info(etcd: EtcdHelper):
    member_ship = MemberShipManager()
    while True:
        try:
            result = etcd.get_prefix("/machine")
            _update_member_ship(member_ship, result)
        except Exception as e:
            logger.error("GetMembersInfo, execption:%s" % e)

        gevent.sleep(SYNC_MEMBER_TIME)
