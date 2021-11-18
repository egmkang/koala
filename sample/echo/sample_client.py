import asyncio
from typing import List, Tuple
from websockets.legacy.client import connect as ws_connect
import json
import random
import io
import hashlib
import random


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


def generate_token(open_id: str, server_id: int, actor_type: str = None, actor_id: str = None) -> bytes:
    d = {"open_id": open_id, "server_id": server_id}
    if actor_type:
        d["actor_type"] = actor_type
    if actor_id:
        d["actor_id"] = actor_id
    check_sum = message_compute_check_sum(d, private_key=PRIVATE_KEY)
    d["check_sum"] = check_sum
    return json.dumps(d).encode("utf-8")


async def echo_client(address: str):
    if random.randint(0, 1000) % 2 == 0:
        token = generate_token("open_id_1", 1)
    else:
        token = generate_token("open_id_2", 2, "IPlayer", "2")

    async with ws_connect(address) as client:
        await client.send(token)
        token = await client.recv()
        print(token)

        while True:
            await client.send(echo[0: random.randint(1, len(echo) - 1)])
            x = await client.recv()
            print(x)
    pass


asyncio.get_event_loop().run_until_complete(echo_client(ADDRESS))
