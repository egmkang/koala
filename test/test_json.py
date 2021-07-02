from koala.json_util import json_dumps, json_loads


class TestJson:
    def test_json_loads_dumps(self):
        t = {"t1": 1, "t2": "2", "t3": [], "t4": {}}
        dumps = json_dumps(t)
        o: dict = json_loads(dumps)
        assert o.get("t1") == t.get("t1")
        assert o.get("t2") == t.get("t2")
        assert o.get("t3") == t.get("t3")
        assert o.get("t4") == t.get("t4")
