import time
import etcd3
import gevent
from .membership import MemberShipManager, MachineInfo
from utils.singleton import Singleton
from utils.log import logger
from entity.entity_type import *
from utils.ujson_codec import *

# TODO: using etcd3


ENTITY_PATH = '/entity/%s_%s'   #/entity/1_1010101, 这种
ENTITY_LOCK_NAME = '%s_%s'


class EntityPosition:
    def __init__(self, entity_type: int, entity_id: int):
        self.entity_type = entity_type
        self.entity_id = entity_id
        self.create_time = int(time.time())
        self.server_unique_id = ""
        self.address = ("", 0)

    @staticmethod
    def create(entity_type: int, entity_id: int, machine: MachineInfo):
        obj = EntityPosition(entity_type, entity_id)
        obj.server_unique_id = machine.unique_id
        obj.address = machine.address
        return obj


@Singleton
class EntityPositionCache:
    def __init__(self):
        self._cache = dict()
        self._membership = MemberShipManager()

    def set_etcd(self, etcd):
        self._etcd = etcd

    def _add_entity_info(self, entity: EntityPosition):
        key = (entity.entity_type, entity.entity_id)
        if key in self._cache:
            old_value: EntityPosition = self._cache[key]
            if old_value.server_unique_id == entity.server_unique_id:
                return
            logger.info("EntityPositionCache.add_entity, Entity:(%s,%s), OldServer:%s, Address:%s" %
                        (entity.entity_type, entity.entity_id, old_value.server_unique_id, old_value.address))
        self._cache[(entity.entity_type, entity.entity_id)] = entity
        logger.info("EntityPositionCache.add_entity, Entity:(%s,%s), NewServer:%s, Address:%s" %
                    (entity.entity_type, entity.entity_id, entity.server_unique_id, entity.address))

    def get_entity_info(self, entity_type:int, entity_id:int) -> EntityPosition:
        key = (entity_type, entity_id)
        if key not in self._cache:
            return None
        return self._cache[key]

    def remove_entity(self, entity_type:int, entity_id:int):
        key = (entity_type, entity_id)
        if key not in self._cache:
            return
        info: EntityPosition = self._cache[key]
        logger.info("EntityPositionCache.remove_entity, Entity:(%s,%s), Server:%s, Address:%s" %
                    (entity_type, entity_id, info.server_unique_id, info.address))
        del self._cache[key]


    # 从Etcd里面获取玩家的位置信息
    def _fetch_entity_pos_from_etcd(self, entity_type: int, entity_id: int) -> EntityPosition:
        path = ENTITY_PATH % (entity_type, entity_id)
        try:
            with self._etcd.get() as client:
                result: etcd.EtcdResult = client.get(path)
                info = CodeUjsonDecode(result.value, EntityPosition)
                return info
        except Exception as e:
            logger.error("fetch_entity_pos_from_etcd, exception:%s" % e)
        return None


    # 先从缓存种获取机器
    # 否则从etcd里面获取机器
    # 并判断Pos的机器有没有失效
    def _check_entity_pos(self, entity_type: int, entity_id: int) -> EntityPosition:
        pos:EntityPosition = self.get_entity_info(entity_type, entity_id)
        if pos is None:
            pos = self._fetch_entity_pos_from_etcd(entity_type, entity_id)
        if pos is None:
            return None
        if self._membership.get_machine_by_unique_id(pos.server_unique_id) is None:
            self.remove_entity(entity_type, entity_id)
            return None
        if pos is not None:
            self._add_entity_info(pos)
        return pos

    def _write_entity_pos(self, pos: EntityPosition):
        path = ENTITY_PATH % (pos.entity_type, pos.entity_id)
        self._add_entity_info(pos)
        try:
            with self._etcd.get() as client:
                client.write(path, CodecUjsonEncode(pos))
        except Exception as e:
            logger.error("write_entity_pos, Entity:(%s,%s), exception:%s" % (pos.entity_type, pos.entity_id, e))

    # 从现在的机器列表里面
    # 按照权重随机一个机器出来
    # 把这个玩家安置到这个机器里面(写入etcd和本地缓存)
    def generate_entity_pos(self, entity_type:int, entity_id: int) -> EntityPosition:
        lock_name = ENTITY_LOCK_NAME % (entity_type, entity_id)
        try:
            with self._etcd.get() as client:
                with etcd.Lock(client, lock_name):
                    pos = self._check_entity_pos(entity_type, entity_id)
                    if pos != None: return pos
                machine = self._membership.random_machine()
                pos = EntityPosition.create(entity_type, entity_id, machine)
                self._write_entity_pos(pos)
                return pos
        except Exception as e:
            logger.error("generate_entity_pos, Entity:(%s,%s), exception:%s" %
                         (entity_type, entity_id, e))
        return None

    # 找到玩家的位置
    # 这边只负责找位置
    # 通讯需要借助其他的设施
    def find_player_pos(self, uid: int) -> EntityPosition:
        position = self._check_entity_pos(ENTITY_TYPE_PLAYER, uid)
        if position is not None:
            return position
        #最大尝试次数
        for x in range(2):
            position = self.generate_entity_pos(ENTITY_TYPE_PLAYER, uid)
            if position is None:
                gevent.sleep(3.0)
        if position is None:
            logger.error("find_player_pos, PlayerID:%s return None" % uid)
        return position

