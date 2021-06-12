from koala import compact_pickle
from dataclasses import dataclass
from koala.message import *
from koala.message.base import SimpleMessage
from typing import Dict, Any


@dataclass
class A(SimpleMessage):
    a: int
    b: float
    c: str
    d: str
    e: float


class TestCompactPickle:
    def test_pickle_dumps(self):
        i: Dict[object, Any] = {1: 1, 2: 2, 3: 3, 4: 4}
        data = compact_pickle.pickle_dumps(i)
        i1 = compact_pickle.pickle_loads(data)
        assert i1 == i

    def test_long_pickle_dumps(self):
        i: Dict[object, Any] = {1: 1, 2: 2, 3: 3, 4: 4, 5: "dsfsdfsdf", "1": 34235, 6: 45345, 10: 4.01,
                                13: [1, 2, 4, 65],
                                15: (1, 2, 3),
                                17: {1: 2, 3: 4, 5: 6}, 8: ["1111111", "1111111", "11111111", "1111111"],
                                19: ("11111111", "11111111", "11111111"), 199: "11111111",
                                20: A(a=10, b=11.0, c="asasasas", d="fgergerg", e=1.1),
                                21: A(a=11, b=11.0, c="11111111", d="11111111", e=2.1)}
        data = compact_pickle.pickle_dumps(i)
        assert data[0:1] == compact_pickle.COMPRESSED
        i1 = compact_pickle.pickle_loads(data)
        assert i1 == i
