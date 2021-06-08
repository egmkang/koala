from koala.network.buffer import Buffer
from koala.network.codec_rpc import CodecRpc
from koala.network.codec_echo import CodecEcho
from koala.network.codec_manager import CodecManager
from koala.network.constant import *


class TestCodec:
    def test_rpc_codec(self):
        codec = CodecRpc()
        data = codec.encode("1234567890")
        msg = codec.decode(Buffer.from_bytes(data))
        assert "1234567890" == msg

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
