from gevent.monkey import patch_all
patch_all()

from net.codec import Codec
from net.tcp_connection import TcpConnection
from net.tcp_server import TcpServer
from utils.buffer import Buffer

class EchoCodec(Codec):
    def __init__(self):
        super().__init__()
        pass

    def encode(self, msg, conn):
        return msg.encode()
        pass

    def decode(self, buffer: Buffer, conn):
        if buffer.readable_length() == 0: return None
        msg = buffer.slice(0).decode()
        buffer.has_read(buffer.readable_length())
        return msg
        pass

def echo_message_handler(conn : TcpConnection, msg):
    print(msg)
    conn.send_message(msg)
    pass


server = TcpServer()
server.listen(18888, EchoCodec(), echo_message_handler)

server.run()
