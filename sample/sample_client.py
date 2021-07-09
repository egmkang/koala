import asyncio
from typing import *
import websockets
import json
import random
import io
import hashlib


PRIVATE_KEY = "1234567890"
ADDRESS = "ws://127.0.0.1:5000/ws"
echo = "1234567890qwertyuiop[]asdfghjkl;'zxcvbnm,"


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


def generate_token(open_id: str, server_id: int) -> bytes:
    d = {"open_id": open_id, "server_id": server_id}
    check_sum = message_compute_check_sum(d, private_key=PRIVATE_KEY)
    d["check_sum"] = check_sum
    return json.dumps(d).encode("utf-8")


async def echo_client(address: str):
    token = generate_token("open_id_1", 1)
    async with websockets.connect(address) as client:
        await client.send(token)
        token = await client.recv()
        print(token)

        while True:
            await client.send(echo[0: random.randint(1, len(echo) - 1)])
            x = await client.recv()
            print(x)
    pass


asyncio.get_event_loop().run_until_complete(echo_client(ADDRESS))
