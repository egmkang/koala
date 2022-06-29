from koala.koala_typing import *
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *


class CodecEcho(Codec):
    def __init__(self):
        super(CodecEcho, self).__init__(CODEC_ECHO)

    def decode(self, buffer: Buffer) -> Optional[object]:
        if buffer.readable_length() > 0:
            mv = buffer.read(buffer.readable_length())
            return str(mv, "utf-8")
        return None

    def encode(self, msg: object) -> bytes:
        s = cast(str, msg)
        return s.encode()
