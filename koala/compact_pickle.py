import pickle
import pickletools

import lz4.frame

THRESHOLD = 300
COMPRESSED = b'1'
UNCOMPRESSED = b'0'


def pickle_dumps(o: object) -> bytes:
    array = pickle.dumps(o, protocol=pickle.HIGHEST_PROTOCOL)
    array = pickletools.optimize(array)
    compressed = UNCOMPRESSED + array
    if len(array) > THRESHOLD:
        compressed = lz4.frame.compress(array)
        if len(compressed) < len(array):
            compressed = COMPRESSED + compressed
    return compressed


def pickle_loads(array: bytes) -> object:
    flag = array[0:1]
    data = array[1:]
    if flag == COMPRESSED:
        data = lz4.frame.decompress(data)
    return pickle.loads(data)


if __name__ == '__main__':
    import pydantic
    from typing import Dict, Any


    class A(pydantic.BaseModel):
        a: int
        b: float
        c: str
        d: str
        e: float


    i: Dict[object, Any] = {1: 1, 2: 2, 3: 3, 4: 4}
    data = pickle_dumps(i)
    print(len(data))
    i1 = pickle_loads(data)
    assert i1 == i

    i: Dict[object, Any] = {1: 1, 2: 2, 3: 3, 4: 4, 5: "dsfsdfsdf", "1": 34235, 6: 45345, 10: 4.01, 13: [1, 2, 4, 65],
                            15: (1, 2, 3),
                            17: {1: 2, 3: 4, 5: 6}, 8: ["1111111", "1111111", "11111111", "1111111"],
                            19: ("11111111", "11111111", "11111111"), 199: "11111111",
                            20: A(a=10, b=11.0, c="asasasas", d="fgergerg", e=1.1),
                            21: A(a=11, b=11.0, c="11111111", d="11111111", e=2.1)}
    data = pickle_dumps(i)
    print(len(data))
    i1 = pickle_loads(data)
    assert i1 == i
