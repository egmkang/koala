from .rpc_codec import RpcRequest, RpcResponse, InitIDGenerator, RpcCodec
from .rpc_client import RpcClient
from .rpc_constant import *
from .rpc_method import get_rpc_method
from net.tcp_server import TcpServer
from net.tcp_connection import TcpConnection
from cluster.entity_position import *
from entity.entity_manager import *
from utils.singleton import Singleton
from utils.log import *
from utils.future import get_future
from utils.local_ip import get_host_ip
from utils.server_unique_id import get_server_unique_id
from entity.entity import *
import logging
import logging.config
import gevent


_position_manager = EntityPositionCache()


def _call_global_method(conn: TcpConnection, fn, request: RpcRequest, response: RpcResponse):
    try:
        result = fn.__call__(*request.args, **request.kwargs)
        # TODO: 看看这边是不是需要支持future
        (response.error_code, response.response) = (ERROR_CODE_SUCCESS, result)
    except Exception as e:
        logger.error("handle_global_method, exception:%s" % e)
        (response.error_code, response.response) = (ERROR_CODE_INTERNAL, None)

    conn.send_message(response)


def _handle_global_method(request: RpcRequest, conn: TcpConnection):
    response = RpcResponse()
    response.request_id = request.request_id

    fn = get_rpc_method(request.entity_type, request.method)
    if fn is None:
        response.error_code = ERROR_CODE_METHOD_NOT_FOUND
        response.response = None
        conn.send_message(response)
        return

    gevent.spawn(lambda: _call_global_method(conn, fn, request, response))


# 返回True表示中断
def _dispatch_entity_method_anyway(entity:Entity, conn: TcpConnection, request:RpcRequest, response:RpcResponse, method):
    try:
        entity.on_active()
    except Exception as e:
        logger.error("dispatch_entity_method, Entity:%s-%s, load fail, exception:%s" %
                     (request.entity_type, request.entity_id, e))
        (response.error_code, response.response) = (ERROR_CODE_ENTITY_LOAD, None)
        conn.send_message(response)
        return True

    try:
        result = method.__call__(entity, *request.args, **request.kwargs)
        # TODO: 看看这边是不是需要支持future
        (response.error_code, response.response) = (ERROR_CODE_SUCCESS, result)
        conn.send_message(response)
    except Exception as e:
        logger.error("dispatch_entity_method, Entity:%s-:%s method:%s, exception:%s" %
                     (request.entity_type, request.request_id, request.method, e))
    return False


def _dispatch_entity_method_loop(entity: Entity):
    context: ActorContext = entity.context()
    if context.running is not False:
        return
    context.running = True

    try:
        while True:
            o = context.queue.get()
            if o is None:
                logger.info("entity:%s-%s exit", (entity.get_entity_type(), entity.get_uid()))
                break
            request: RpcRequest = o[1]

            context.host = request.host
            context.request_id = request.request_id

            need_break = _dispatch_entity_method_anyway(entity, *o)
            if need_break:
                break

            context.host = None
            context.request_id = None

    except Exception as e:
        logger.error("dispatch_entity_method_loop, entity:%s-%s, Exception:%s",
                     (entity.get_entity_type(), entity.get_uid(), e))
    entity.context().running = False
    pass


def _handle_entity_method(request: RpcRequest, conn: TcpConnection):
    response = RpcResponse()
    response.request_id = request.request_id
    #logger.info("handle entity method, entity:%s-%s, Method:%s" % (request.entity_type, request.entity_id, request.method))

    method = get_rpc_method(request.entity_type, request.method)
    if method is None:
        (response.error_code, response.response) = (ERROR_CODE_METHOD_NOT_FOUND, None)
        conn.send_message(response)
        return

    manager: EntityManager = get_entity_manager(request.entity_type)
    entity: Entity = manager.get_or_new_entity(request.entity_id)
    if entity is None:
        (response.error_code, response.response) = (ERROR_CODE_ENTITY_NOT_FOUND, None)
        conn.send_message(response)
        return

    if entity.context().running is False:
        gevent.spawn(lambda: _dispatch_entity_method_loop(entity))

    if entity.context().host == request.host and entity.context().request_id <= request.request_id:
        gevent.spawn(lambda: _dispatch_entity_method_anyway(entity, conn, request, response, method))
        return
    entity.context().send_message((conn, request, response, method))


def rpc_message_dispatcher(conn: TcpConnection, msg):
    if isinstance(msg, RpcRequest):
        _dispatch_request(conn, msg)
        pass
    else:
        future = get_future(msg.request_id)
        if future is None:
            logger.error("dispatch rpc response: %s, future not found" % (msg.request_id))
            return
        future.set_result(msg)
    pass


def _dispatch_request(conn: TcpConnection, request: RpcRequest):
    if request.entity_type == RPC_ENTITY_TYPE_GLOBAL:
        _handle_global_method(request, conn)
    else:
        # TODO:
        # 这边要支持多种Actor
        _handle_entity_method(request, conn)


@Singleton
class RpcServer(TcpServer):
    def __init__(self, server_id):
        super().__init__()
        self.server_id = server_id
        self.client_pool = dict()
        InitIDGenerator(server_id)
        self._init_logger()
        self._init_machine_info()
        logger.info("ServerID:%d init" % server_id)
        logger.info("ServerUniqueID:%s init" % get_server_unique_id())

    def _init_machine_info(self):
        self.machine_info = MachineInfo(self.server_id)
        self.machine_info.unique_id = get_server_unique_id()
        self.etcd = EtcdHelper(host="119.27.187.221", port=2379)

    def _init_logger(self):
        logging.config.dictConfig(LOGGING_CONFIG_DEFAULTS)

    def listen_port(self, port):
        logger.info("listen port:%s" % port)
        self.listen(port, RpcCodec(), rpc_message_dispatcher)
        if self.machine_info.address is None:
            self.machine_info.address = (get_host_ip(), port)

    def rpc_connect(self, host, port):
        key = (host, port)
        if key not in self.client_pool:
            client = RpcClient(host, port)
            self.client_pool[key] = client
            return client
        return self.client_pool[key]

    def _rpc_connection_gc_once(self):
        current_time = time.time() - 60
        try:
            gc_list = list()
            for (key, client) in self.client_pool.items():
                if client.last_active_time < current_time:
                    gc_list.append((key, client))

            for (key, client) in gc_list:
                logger.info("rpc_connection_gc_once, Client:%s", key)
                del self.client_pool[key]
                client.close()
        except Exception as e:
            logger.error("rpc_connection_gc_once, exception:%s" % e)
        pass

    def rpc_connection_gc(self):
        while True:
            # 需要把不存活的链接干掉
            gevent.sleep(60.0)
            self._rpc_connection_gc_once()
        pass

    def run(self):
        _position_manager.set_etcd(self.etcd)
        gevent.spawn(lambda: update_machine_member_info(self.machine_info, self.etcd))
        gevent.spawn(lambda: get_members_info(self.etcd))
        gevent.spawn(lambda: self.rpc_connection_gc())

        while True:
            gevent.sleep(1.0)

