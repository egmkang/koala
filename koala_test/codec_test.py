from koala.network.buffer import Buffer
from koala.network.codec_rpc import CodecRpc, Message
from koala.network.codec_echo import CodecEcho
from koala.network.codec_manager import CodecManager
from koala.network.constant import *
from koala.message import *


class TestCodec:
    def test_rpc_codec(self):
        codec = CodecRpc()
        heart_beat = HeartBeatRequest()
        heart_beat.milli_seconds = 1212123
        data = codec.encode((heart_beat, None))
        msg, body = cast(Message, codec.decode(Buffer.from_bytes(data)))
        msg = cast(HeartBeatRequest, msg)
        assert heart_beat.milli_seconds == msg.milli_seconds
        assert body is None or body == b''

    def test_echo_codec(self):
        codec = CodecEcho()
        data = codec.encode("1234567890")
        msg = codec.decode(Buffer.from_bytes(data))
        assert "1234567890" == msg

    def test_codec_manager(self):
        manager = CodecManager()
        s = "11223344556677889900"
        codec = manager.get_codec(CODEC_RPC)
        data = codec.encode(s)
        msg = codec.decode(Buffer.from_bytes(data))
        assert s == msg

        codec = manager.get_codec(CODEC_ECHO)
        data = codec.encode(s)
        msg = codec.decode(Buffer.from_bytes(data))
        assert s == msg


t = TestCodec()
t.test_rpc_codec()
