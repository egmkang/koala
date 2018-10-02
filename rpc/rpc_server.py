from .rpc_connection import RpcConnection
from .rpc_codec import RpcRequest, RpcResponse, InitIDGenerator
from .rpc_client import RpcClient
from .rpc_constant import *
from .rpc_loop import *
from cluster.membership import *
from cluster.etcd_client import *
from cluster.entity_position import *
from entity.player_manager import *
from utils.singleton import Singleton
from utils.log import *
from utils.local_ip import GetHostIp
from entity.entity import *
import logging
import logging.config
import uuid


_global_method = dict()
_global_player_method = dict()
_player_manager = PlayerManager()
_position_manager = EntityPositionCache()


def rpc_method(fn):
    global _global_method
    name = fn.__name__
    _global_method[name] = fn
    return fn

def player_rpc_method(fn):
    global _global_player_method
    name = fn.__name__
    _global_player_method[name] = fn
    return fn

async def _call_global_method(conn: RpcConnection, request: RpcRequest, response: RpcResponse):
    method = _global_method[request.method]
    try:
        result = method.__call__(*request.args, **request.kwargs)
        if asyncio.iscoroutine(result):
            result = asyncio.wait_for(result, 5, loop)
        (response.error_code, response.response) = (ERROR_CODE_SUCCESS, result)
    except Exception as e:
        logger.error("handle_global_method, exception:%s" % e)
        (response.error_code, response.response) = (ERROR_CODE_INTERNAL, None)

    await conn.send_message(response)

async def _handle_global_method(request: RpcRequest, conn: RpcConnection):
    response = RpcResponse()
    response.request_id = request.request_id

    if request.method not in _global_method:
        response.error_code = ERROR_CODE_METHOD_NOT_FOUND
        response.response = None
        await conn.send_message(response)
        return

    loop.create_task(_call_global_method(conn, request, response))


#返回True表示中断
async def _dispatch_entity_method_anyway(entity:Entity, conn: RpcConnection, request:RpcRequest, response:RpcResponse, method):
    try:
        await entity.load_from_db()
    except Exception as e:
        logger.error("dispatch_entity_method, Entity:%s-%s, load fail, exception:%s" %
                     (request.entity_type, request.entity_id, e))
        (response.error_code, response.response) = (ERROR_CODE_PLAYER_LOAD, None)
        await conn.send_message(response)
        return True

    try:
        result = method.__call__(entity, *request.args, **request.kwargs)
        if asyncio.iscoroutine(result):
            result = await asyncio.wait_for(result, 5, loop)
        (response.error_code, response.response) = (ERROR_CODE_SUCCESS, result)
        await conn.send_message(response)
    except Exception as e:
        logger.error("dispatch_entity_method, Entity:%s-:%s method:%s, exception:%s" %
                     (request.entity_type, request.request_id, request.method, e))
    return False

async def _dispatch_entity_method_loop(entity: Entity):
    context: RpcContext = entity.context()
    if context.running != False:
        return
    context.running = True

    try:
        while True:
            o = await context.queue.get()
            if o is None:
                logger.info("entity:%s-%s exit", (entity.get_entity_type(), entity.get_uid()))
                break
            request: RpcRequest = o[1]

            context.host = request.host
            context.request_id = request.request_id

            need_break = await _dispatch_entity_method_anyway(entity, *o)
            if need_break: break

            context.host = None
            context.request_id = None

    except Exception as e:
        logger.error("dispatch_entity_method_loop, entity:%s-%s, Exception:%s",
                     (entity.get_entity_type(), entity.get_uid(), e))
    entity.context().running = False
    pass

async def _handle_player_method(request: RpcRequest, conn: RpcConnection):
    response = RpcResponse()
    logger.info("handle player method, Player:%s, Method:%s" % (request.entity_id, request.method))
    if request.method not in _global_player_method:
        (response.error_code, response.response) = (ERROR_CODE_METHOD_NOT_FOUND, None)
        await conn.send_message(response)
        return

    method = _global_player_method[request.method]
    player:Player = _player_manager.get_or_new_player(request.entity_id)
    if player == None:
        (response.error_code, response.response) = (ERROR_CODE_PLAYER_NOT_FOUND, None)
        await conn.send_message(response)
        return

    if player.context().running == False:
        loop.create_task(_dispatch_entity_method_loop(player))

    if player.context().host == request.host and player.context().request_id <= request.request_id:
        loop.create_task(_dispatch_entity_method_anyway(player, conn, request, response, method))
        return
    await player.context().SendMessage((conn, request, response, method))


async def _dispatch_request(conn: RpcConnection, request: RpcRequest):
    if request.entity_type == RPC_ENTITY_TYPE_GLOBAL:
        await _handle_global_method(request, conn)
    if request.entity_type == RPC_ENTITY_TYPE_PLAYER:
        await _handle_player_method(request, conn)


async def _run_rpc_conn(conn: RpcConnection):
    while True:
        request = await conn.recv_message()
        if request == None:
            conn.close()
            return
        await _dispatch_request(conn, request)


async def _rpc_handle(reader: asyncio.StreamReader, writer: asyncio.StreamWriter):
    conn = RpcConnection(reader, writer)
    try:
        await _run_rpc_conn(conn)
    except Exception as e:
        logger.error("_rpc_handle %s" % e)
    finally:
        conn.close()

_server_unique_id = ""

def GetServerUniqueID():
    global _server_unique_id
    if len(_server_unique_id) <= 0:
        _server_unique_id = str(uuid.uuid4())
    return _server_unique_id


@Singleton
class RpcServer:
    def __init__(self, server_id):
        self.loop = get_loop()
        self.server_id = server_id
        self.client_pool = dict()
        InitIDGenerator(server_id)
        self._init_logger()
        self._init_machine_info()
        logger.info("ServerID:%d init" % server_id)
        logger.info("ServerUniqueID:%s init" % GetServerUniqueID())

    def _init_machine_info(self):
        self.machine_info = MachineInfo(self.server_id)
        self.machine_info.unique_id = GetServerUniqueID()
        self.etcd = EtcdClient(host="119.27.187.221", port=2379)

    def _init_logger(self):
        logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)

    def listen(self, port):
        logger.info("listen port:%s" % port)
        co = asyncio.start_server(_rpc_handle, host="0.0.0.0", port=port, loop=self.loop, limit=RPC_WINDOW_SIZE)
        if self.machine_info.address == None:
            self.machine_info.address = (GetHostIp(), port)
        self.loop.create_task(co)

    #TODO:
    #需要有机制删除RpcConnection
    def rpc_connect(self, host, port):
        key = (host, port)
        if key not in self.client_pool:
            client = RpcClient(host, port, self.loop)
            self.client_pool[key] = client
            return client
        return self.client_pool[key]

    def create_task(self, co):
        self.loop.create_task(co)

    def run(self):
        _position_manager.set_etcd(self.etcd)
        self.create_task(UpdateMachineMemberInfo(self.machine_info, self.etcd))
        self.create_task(GetMembersInfo(self.etcd))
        self.loop.run_forever()

