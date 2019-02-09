import time
from datetime import datetime

TimeSecondsBegin = (datetime(year=2019, month=1, day=1) - datetime(1970, 1, 1)).total_seconds()


class IdGenerator:
    """
    id = seconds * 100000000 + server * 10000 + seeds
    """
    def __init__(self, server_id):
        self.server_id = server_id
        self.seconds = IdGenerator._get_seconds()
        self.seeds = 0
        self._gen_id()

    def NextId(self):
        sec = IdGenerator._get_seconds()
        if self.seconds != sec:
            self.seconds = sec
            self.seeds = 0
            self._gen_id()
        self.id += 1
        return self.id

    def _gen_id(self):
        self.id = self.seconds * 100000000 + self.server_id * 10000 + self.seeds

    @staticmethod
    def _get_seconds():
        seconds = int(time.time()) - TimeSecondsBegin
        return int(seconds)
