from typing import Optional
from koala.singleton import Singleton
from koala.network.codec import Codec
from koala.network.codec_echo import CodecEcho
from koala.network.codec_rpc import CodecRpc


@Singleton
class CodecManager:
    def __init__(self):
        self._dict = dict()
        self._register()
        pass

    def _register(self):
        self.register_codec(CodecRpc())
        self.register_codec(CodecEcho())

    def register_codec(self, codec: Codec):
        self._dict[codec.codec_id] = codec

    def get_codec(self, codec_id: int) -> Optional[Codec]:
        if codec_id in self._dict:
            return self._dict[codec_id]
