from typing import cast
from koala.network.codec import Codec
from koala.network.buffer import Buffer
from koala.network.constant import *


class GatewayRawMessage:
    data = b""


# 暂时先用Echo的位置
# 后面再抽象编解码器
class GatewayCodec(Codec):
    def __init__(self):
        super().__init__(CODEC_GATEWAY)
        pass

    def codec_id(self) -> int:
        return CODEC_GATEWAY
        pass

    def decode(self, buffer: Buffer) -> object:
        data = buffer.read(buffer.readable_length())
        obj = GatewayRawMessage()
        obj.data = data
        return obj

    def encode(self, msg: object) -> bytes:
        if isinstance(msg, bytes):
            return msg
        raw_msg = cast(GatewayRawMessage, msg)
        return raw_msg.data
