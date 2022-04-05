import asyncio
from typing import Any, List, Tuple, Dict
from websockets.legacy.client import connect as ws_connect
import json
import random
import io
import hashlib


PRIVATE_KEY = "1234567890"
ADDRESS = "ws://127.0.0.1:5001/ws"
echo = "1234567890qwertyuiop[]asdfghjkl;'zxcvbnm,"
count = 0


def message_compute_check_sum(
    message: Dict[str, Any], private_key: str, escape_key: str = "check_sum"
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


def generate_token(
    open_id: str, server_id: int, actor_type: str = "", actor_id: str = ""
) -> bytes:
    d = {"open_id": open_id, "server_id": server_id}
    if actor_type:
        d["actor_type"] = actor_type
    if actor_id:
        d["actor_id"] = actor_id
    check_sum = message_compute_check_sum(d, private_key=PRIVATE_KEY)
    d["check_sum"] = check_sum
    return json.dumps(d).encode("utf-8")


async def qps():
    await asyncio.sleep(1.0)
    c = count
    while True:
        new_value = count
        if new_value != c:
            print(new_value - c)
            c = new_value
        await asyncio.sleep(1.0)


async def echo_client(address: str):
    if random.randint(0, 1000) % 2 == 0:
        token = generate_token("open_id_1", 1)
    else:
        token = generate_token("open_id_2", 2, "IPlayer", "2")

    global count

    async with ws_connect(address) as client:
        await client.send(token)
        token = await client.recv()
        print(token)

        while True:
            await client.send(echo[0 : random.randint(1, len(echo) - 1)])
            await client.recv()
            count += 1


asyncio.get_event_loop().create_task(qps())
asyncio.get_event_loop().run_until_complete(echo_client(ADDRESS))
