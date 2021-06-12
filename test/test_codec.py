from koala.network.buffer import Buffer
from koala.message import *
from koala.message.rpc_protocol import RpcProtocol
from koala.network.codec_rpc import CodecRpc, Message
from koala.network.codec_echo import CodecEcho
from koala.network.codec_manager import CodecManager
from koala.network.constant import *
from koala.message import *


class TestRpcProtocol:
    def test_rpc_protocol_message(self):
        req = RpcRequest()
        body = b"121212"
        rpc_message = RpcProtocol.from_msg(req, body)
        assert rpc_message.__class__ == req.__class__


class TestCodec:
    def test_rpc_codec(self):
        codec = CodecRpc()
        heart_beat = HeartBeatRequest()
        heart_beat.milli_seconds = 1212123
        data = codec.encode((heart_beat, None))
        t, (msg, body) = cast(Tuple[Type, Optional[Message]], codec.decode(Buffer.from_bytes(data)))
        msg = cast(HeartBeatRequest, msg)
        assert heart_beat.milli_seconds == msg.milli_seconds
        assert body is None or body == b''

    def test_echo_codec(self):
        codec = CodecEcho()
        data = codec.encode("1234567890")
        t, msg = codec.decode(Buffer.from_bytes(data))
        assert "1234567890" == msg

    def test_codec_manager(self):
        manager = CodecManager()
        rpc_input = (HeartBeatRequest(), b"11223344556677889900")
        codec = manager.get_codec(CODEC_RPC)
        data = codec.encode(rpc_input)
        t, (msg, body) = codec.decode(Buffer.from_bytes(data))
        assert rpc_input == (msg, body)

        s = "11223344556677889900"
        codec = manager.get_codec(CODEC_ECHO)
        data = codec.encode(s)
        t, msg = codec.decode(Buffer.from_bytes(data))
        assert s == msg
