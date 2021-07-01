from koala.network.buffer import Buffer
from koala.message import *
from koala.message.rpc_message import RpcMessage
from koala.network.codec_rpc import CodecRpc
from koala.network.codec_echo import CodecEcho
from koala.network.codec_manager import CodecManager
from koala.network.constant import *
from koala.message import *


class TestRpcProtocol:
    def test_rpc_protocol_message(self):
        req = RpcRequest()
        body = b"121212"
        rpc_message = RpcMessage.from_msg(req, body)
        assert rpc_message.meta.__class__ == req.__class__


class TestCodec:
    def test_rpc_codec(self):
        codec = CodecRpc()
        heart_beat = RequestHeartBeat()
        heart_beat.milli_seconds = 1212123
        data = codec.encode(RpcMessage.from_msg(heart_beat, None))
        decoded_msg = cast(RpcMessage, codec.decode(Buffer.from_bytes(data)))
        msg = cast(RequestHeartBeat, decoded_msg.meta)
        assert heart_beat.milli_seconds == msg.milli_seconds
        assert decoded_msg.body is None or decoded_msg.body == b''

    def test_echo_codec(self):
        codec = CodecEcho()
        data = codec.encode("1234567890")
        msg = codec.decode(Buffer.from_bytes(data))
        assert "1234567890" == msg

    def test_codec_manager(self):
        manager = CodecManager()
        rpc_input = RpcMessage.from_msg(RequestHeartBeat(), b"11223344556677889900")
        codec = manager.get_codec(CODEC_RPC)
        data = codec.encode(rpc_input)
        msg = cast(RpcMessage, codec.decode(Buffer.from_bytes(data)))
        assert rpc_input.meta == msg.meta
        assert rpc_input.body == msg.body

        s = "11223344556677889900"
        codec = manager.get_codec(CODEC_ECHO)
        data = codec.encode(s)
        msg = codec.decode(Buffer.from_bytes(data))
        assert s == msg
