from typing import Optional
from koala import default_dict
from koala.singleton import Singleton
from koala.network.codec import Codec
from koala.network.codec_echo import CodecEcho
from koala.network.codec_rpc import CodecRpc


class CodecManager(Singleton):
    def __init__(self):
        super(CodecManager, self).__init__()
        self._dict: default_dict.DefaultDict[int, Codec] = default_dict.DefaultDict()
        self._register()
        pass

    def _register(self):
        self.register_codec(CodecRpc())
        self.register_codec(CodecEcho())

    def register_codec(self, codec: Codec):
        self._dict[codec.codec_id] = codec

    def get_codec(self, codec_id: int) -> Optional[Codec]:
        if self._dict.contains_key(codec_id):
            return self._dict[codec_id]
        return None
