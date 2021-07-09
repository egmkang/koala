from koala.typing import *
from koala.json_util import json_loads
import io
import hashlib


def message_compute_check_sum(message: dict, private_key: str, escape_key: str = "check_sum") -> str:
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


def message_check_sum(raw_message: bytes, private_key: str, check_sum_key: str = "check_sum") -> (dict, bool):
    message: dict = json_loads(raw_message)
    input_check_sum = ""
    for (k, v) in message.items():
        if k == check_sum_key:
            input_check_sum = "%s" % v
            break

    check_sum = message_compute_check_sum(message, private_key, check_sum_key)
    return message, check_sum == input_check_sum
