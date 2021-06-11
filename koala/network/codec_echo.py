from koala.typing import *
from koala.network.buffer import Buffer
from koala.network.codec import Codec
from koala.network.constant import *


class CodecEcho(Codec):
    def __init__(self):
        super(CodecEcho, self).__init__(CODEC_ECHO)

    def decode(self, buffer: Buffer) -> Tuple[Type, Optional[object]]:
        if buffer.readable_length() > 0:
            return str.__class__, buffer.read(buffer.readable_length()).decode()
        return str.__class__, None

    def encode(self, msg: object) -> bytes:
        s = cast(str, msg)
        return s.encode()
