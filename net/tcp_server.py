import gevent
from gevent.server import StreamServer
from .codec import Codec
from .tcp_connection import TcpConnection


class TcpServer(object):
    def __init__(self):
        self.server = None
        pass

    def _handle_new_connection(self, socket, codec: Codec, processor):
        conn = TcpConnection(socket, codec, processor)
        conn.run()
        pass

    def listen(self, port, codec: Codec, processor):
        def server_handler(socket, _):
            self._handle_new_connection(socket, codec, processor)
            pass
        self.server = StreamServer(("0.0.0.0", port), server_handler)
        gevent.spawn(lambda: self.server.serve_forever())

    def run(self):
        while True:
            gevent.sleep(1.0)
