import pickle
import pickletools
from koala.typing import *
import lz4.frame

THRESHOLD = 300
COMPRESSED = b'1'
UNCOMPRESSED = b'0'


def pickle_dumps(o: Any) -> bytes:
    array = pickle.dumps(o, protocol=pickle.HIGHEST_PROTOCOL)
    # array = pickletools.optimize(array)
    compressed = UNCOMPRESSED + array
    if len(array) > THRESHOLD:
        compressed = lz4.frame.compress(array)
        if len(compressed) < len(array):
            compressed = COMPRESSED + compressed
    return compressed


def pickle_loads(array: bytes) -> Any:
    flag = array[0:1]
    data = array[1:]
    if flag == COMPRESSED:
        data = lz4.frame.decompress(data)
    return pickle.loads(data)
