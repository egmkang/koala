import pylru


def test_pylru():
    lru = pylru.lrucache(10)

    assert not lru.get(1)
    lru[1] = 100
    assert lru.get(1) == 100

    del lru[1]
    assert not lru.get(1)

    lru[1] = 100
    lru.pop(1)
    assert not lru.get(1)
    pass
