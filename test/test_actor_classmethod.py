from koala.server.actor_base import ActorBase


class SubClass0(ActorBase):
    pass


class SubClass1(ActorBase):
    @classmethod
    def gc_time(cls) -> int:
        return 30

    @classmethod
    def actor_weight(cls) -> int:
        return 10


class SubClass2(ActorBase):
    @classmethod
    def gc_time(cls) -> int:
        return 3000

    @classmethod
    def actor_weight(cls) -> int:
        return 11


def test_actor_abstractclassmethod():
    actor0 = SubClass0()
    assert actor0.gc_time() == 30 * 60
    assert actor0.actor_weight() == 1

    actor1 = SubClass1()
    assert actor1.gc_time() == 30
    assert actor1.actor_weight() == 10

    actor2 = SubClass2()
    assert actor2.gc_time() == 3000
    assert actor2.actor_weight() == 11
