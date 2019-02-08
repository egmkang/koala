import socket
import gevent
from gevent.event import AsyncResult
from .rpc_codec import *
from net.tcp_connection import TcpConnection
from utils.log import logger
from utils.future import add_future


class RpcClient:
    def __init__(self, host, port):
        self._conn = None
        self._host = host
        self._port = port
        self._connecting = False

    def connect(self):
        from .rpc_server import rpc_message_dispatcher

        if self._conn is not None:
            return
        if not self._connecting:
            self._connecting = True
            logger.info("connect:%s:%s" % (self._host, self._port))
            sock = socket.socket()
            sock.connect((self._host, self._port))
            logger.info("connect:%s:%s complete" % (self._host, self._port))
            self._conn = TcpConnection(sock, RpcCodec(), rpc_message_dispatcher)
            gevent.spawn(lambda: self._conn.run())
            self._connecting = False

        while True:
            if self._conn is not None:
                return
            gevent.sleep(0.1)

    def close(self):
        if self._conn is None:
            pass
        self._conn.close()

    def _recv_message(self):
        try:
            self._conn.recv_message()
        except Exception as e:
            logger.error("RpcClient.recv_message, Exception:%s" % (e))
            self._conn.close()
            self._conn = None

    def send_request(self, host, request_id, entity_type, entity_id, method, *args, **kwargs):
        self.connect()

        from .rpc_server import GetServerUniqueID

        request = RpcRequest()
        if host is not None:
            request.host = host
        else:
            request.host = GetServerUniqueID()

        if request_id is not None:
            request.request_id = request_id

        request.entity_type = entity_type
        request.entity_id = entity_id
        request.method = method
        request.args = args
        request.kwargs = kwargs

        self._conn.send_message(request)

        future = AsyncResult()

        add_future(request.request_id, future)

        future.wait(5)

        resp: RpcResponse = future.get()
        return resp.response
