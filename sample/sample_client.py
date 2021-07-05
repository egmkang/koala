import asyncio
import websockets
import json
import random

ADDRESS = "ws://127.0.0.1:5000/ws"
echo = "1234567890qwertyuiop[]asdfghjkl;'zxcvbnm,"


async def echo_client(address: str):
    async with websockets.connect(address) as client:
        token = json.dumps({"open_id": "open_id_1", "server_id": 1}).encode("utf-8")
        await client.send(token)
        token = await client.recv()
        print(token)

        while True:
            await client.send(echo[0: random.randint(1, len(echo) - 1)])
            x = await client.recv()
            print(x)
    pass


asyncio.get_event_loop().run_until_complete(echo_client(ADDRESS))
