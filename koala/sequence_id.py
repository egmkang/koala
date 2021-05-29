
class SequenceId(object):
    SHIFT = 1000000000

    def __init__(self):
        self._seed = 0
        self._id = 0

    def new_id(self) -> int:
        self._id += 1
        return self._id

    @property
    def seed(self):
        return self._seed

    def set_seed(self, seed: int):
        if seed <= self._seed:
            raise Exception("seed cannot decrease")
        self._seed = seed
        self._id = self._seed * self.SHIFT
        pass
