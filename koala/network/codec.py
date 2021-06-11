from abc import ABC, abstractmethod
from koala.typing import *
from koala.network.buffer import Buffer


class Codec(ABC):
    def __init__(self, codec_id: int):
        super(Codec, self).__init__()
        self._codec_id = codec_id
        pass

    @property
    def codec_id(self) -> int:
        return self._codec_id

    # (Buffer) => object
    @abstractmethod
    def decode(self, buffer: Buffer) -> Tuple[Type, Optional[object]]:
        pass

    # (msg) => bytes
    @abstractmethod
    def encode(self, msg: object) -> bytes:
        pass

