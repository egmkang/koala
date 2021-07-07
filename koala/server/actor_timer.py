import asyncio
import gc
import time
import weakref

from koala.typing import *
from koala.logger import logger


__TIMER_ID = 0


def _gen_timer_id() -> int:
    global __TIMER_ID
    __TIMER_ID += 1
    return __TIMER_ID


def _milli_seconds() -> int:
    return int(time.time() * 1000)


class ActorTimer:
    def __init__(self, weak_actor: weakref.ReferenceType,
                 actor_id: str,
                 manager: "ActorTimerManager",
                 fn: Callable[["ActorTimer"], None],
                 interval: int):
        self._timer_id = _gen_timer_id()
        self._weak_actor = weak_actor
        self._actor_id = actor_id
        self._manager = manager
        self._fn = fn
        self._interval = interval
        self._begin_time = _milli_seconds()
        self._tick_count = 0
        self._is_cancel = False

    def __del__(self):
        logger.debug("ActorTimer:%s GC, ActorID:%s" % (self.timer_id, self._actor_id))
        pass

    @property
    def timer_id(self) -> int:
        return self._timer_id

    @property
    def tick_count(self) -> int:
        return self._tick_count

    @property
    def interval(self) -> int:
        return self._interval

    @property
    def is_cancel(self) -> bool:
        return self._is_cancel or not self._weak_actor()

    def cancel(self):
        self._is_cancel = True

    def tick(self):
        if self.is_cancel:
            return
        try:
            self._tick_count += 1
            self._fn(self)
        except Exception as e:
            logger.error("ActorTimer, Actor:%s, ActorID:%d, Exception:%s" %
                         (self._actor_id, self.timer_id, e))
            return
        if not self.is_cancel:
            next_wait = self.next_tick_time()
            self._manager.internal_register_timer(next_wait, self)
    pass

    def run(self):
        actor = self._weak_actor()
        if actor:
            asyncio.create_task(actor.context.push_message((None, self)))
        else:
            self.cancel()

    def next_tick_time(self) -> int:
        current = _milli_seconds()
        next_time = self._begin_time + (self._tick_count + 1) * self._interval
        wait_time = next_time - current
        return wait_time if wait_time > 0 else 0


class ActorTimerManager:
    def __init__(self, weak_actor: weakref.ReferenceType):
        self._weak_actor = weak_actor
        self._actor_id = ""
        self._dict: Dict[int, ActorTimer] = dict()

    @property
    def actor_id(self) -> str:
        if self._actor_id == "":
            actor = self._weak_actor()
            self._actor_id = "%s/%s" % (actor.type_name, actor.uid)
        return self._actor_id

    @classmethod
    async def _run_timer(cls, sleep: int, timer: ActorTimer):
        if sleep > 0:
            await asyncio.sleep(sleep/1000)
        timer.run()

    def internal_register_timer(self, next_time: int, timer: ActorTimer):
        asyncio.create_task(self._run_timer(next_time, timer))

    def register_timer(self, interval: int, fn: Callable[[ActorTimer], None]) -> ActorTimer:
        timer = ActorTimer(self._weak_actor, self.actor_id, self, fn, interval)
        self._dict[timer.timer_id] = timer

        next_wait = timer.next_tick_time()
        self.internal_register_timer(next_wait, timer)
        return timer

    def unregister_timer(self, timer_id: int):
        if timer_id in self._dict:
            timer = self._dict[timer_id]
            self._dict.pop(timer_id)
            timer.cancel()

    def unregister_all(self):
        remove_list = []
        for timer_id in self._dict:
            remove_list.append(timer_id)
        for timer_id in remove_list:
            self.unregister_timer(timer_id)
        del self._dict
        self._dict = None

