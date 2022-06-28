import pickle
from zstd import ZSTD_compress, ZSTD_uncompress
from koala.koala_typing import *
import io
import hashlib
import socket
import json
from typing import Any, Callable, cast, List, Tuple

json_dumps: Callable[[Any], bytes] = cast(Callable[[Any], bytes], None)
json_loads: Callable[[str | bytes], Any] = cast(Callable[[str | bytes], Any], None)
_local_ip = ""

THRESHOLD = 300
COMPRESSED = b"1"
UNCOMPRESSED = b"0"


try:
    import orjson

    json_loads = orjson.loads
    json_dumps = orjson.dumps
except:

    def _dumps(o):
        return json.dumps(o).encode()  # type: ignore

    def _loads(b):
        return json_loads(b.decode())  # type: ignore

    json_loads = _loads  # type: ignore
    json_dumps = _dumps  # type: ignore
    pass


def get_host_ip(host: str = "", port: int = 0):
    global _local_ip
    if len(_local_ip) > 4:
        return _local_ip

    if not host:
        host = "8.8.8.8"
    if not port:
        port = 80
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, port))
        ip = s.getsockname()[0]
        _local_ip = ip
    finally:
        s.close()
    return _local_ip


def to_dict(obj: Any) -> Dict | List:
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif getattr(obj, "__slots__", None):
        return {
            name: to_dict(getattr(obj, name))
            for name in obj.__slots__
            if not name.startswith("_")
        }
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__dict__"):
        return {
            k: to_dict(v)
            for k, v in obj.__dict__.items()
            if not callable(v) and not k.startswith("_")
        }
    elif not isinstance(obj, str) and hasattr(obj, "__iter__"):
        return [to_dict(v) for v in obj]
    else:
        return cast(Dict, obj)


def message_compute_check_sum(
    message: dict, private_key: str, escape_key: str = "check_sum"
) -> str:
    item: List[Tuple[str, str]] = list()
    for (k, v) in message.items():
        if k == escape_key:
            continue
        item.append(("%s" % k, "%s" % v))

    item.sort(key=lambda i: i[0])
    item.append((private_key, ""))

    writer = io.StringIO()
    for (k, v) in item:
        writer.write(k)
        writer.write(v)
    input_str = writer.getvalue()

    check_sum = hashlib.sha256(input_str.encode("utf-8"))
    return check_sum.hexdigest()


def message_check_sum(
    raw_message: bytes, private_key: str, check_sum_key: str = "check_sum"
) -> Tuple[dict, bool]:
    message: dict = json_loads(raw_message)
    input_check_sum: str = ""
    for k, v in message.items():
        if k == check_sum_key:
            input_check_sum = cast(str, "%s" % v)
            break

    check_sum = message_compute_check_sum(message, private_key, check_sum_key)
    return message, check_sum == input_check_sum


def pickle_dumps(o: Any) -> bytes:
    array = pickle.dumps(o, protocol=pickle.HIGHEST_PROTOCOL)
    # array = pickletools.optimize(array)
    compressed = UNCOMPRESSED + array
    if len(array) > THRESHOLD:
        compressed = ZSTD_compress(array, 1)
        if len(compressed) < len(array):
            compressed = COMPRESSED + compressed
    return compressed


def pickle_loads(array: bytes) -> Any:
    flag = array[0:1]
    data = array[1:]
    if flag == COMPRESSED:
        data = ZSTD_uncompress(data)
    return pickle.loads(data)
