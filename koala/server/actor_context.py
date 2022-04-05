import time
from asyncio import Queue


class ActorContext(object):
    def __init__(self):
        self.mailbox = Queue()
        self.loop_id = 0
        self.reentrant_id = 0
        self.last_message_time = time.time()

    async def pop_message(self) -> object:
        return await self.mailbox.get()

    async def push_message(self, msg: object):
        await self.mailbox.put(msg)
