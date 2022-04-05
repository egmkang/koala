import pytest
from koala.readonly import *
import pickle


class TestReadOnly:
    def test_list(self):
        l1 = ReadOnlyList([1, 2, 3])
        assert l1 == [1, 2, 3]
        assert type(l1) == ReadOnlyList

        l2 = ReadOnlyList([[1, 2], [2, 3], [3, 4]])
        assert len(l2) == 3
        assert type(l2[0]) == ReadOnlyList

        l3 = ReadOnlyList(ReadOnlyList([1, 2, 3]))
        assert l3 == [1, 2, 3]
        assert type(l3) == ReadOnlyList

        with pytest.raises(ReadOnlyException):
            l1[0] = 10

    def test_dict(self):
        d1 = ReadOnlyDict(ReadOnlyDict({1: 1, 2: 2, 3: 3}))
        assert d1 == {1: 1, 2: 2, 3: 3}

        with pytest.raises(ReadOnlyException):
            d1[1] = 10

    def test_object(self):
        class AccessItem(ReadOnlyObject):
            id: int = 0
            title1: str = ""
            list_in_list: List[List[str]] = []
            dict_in_dict: Dict[str, Dict[str, int]] = {}
            dict_in_list: List[Dict[str, int]] = []
            list_in_dict: Dict[str, List[int]] = {}

        test_data1 = {
            "id": 12,
            "title1": "haha",
            "list_in_list": [["123"], ["456"]],
            "dict_in_dict": {"123": {"456": 1}},
            "dict_in_list": [{"str": 1234}],
            "list_in_dict": {"list": [1, 2, 3]},
        }

        item = AccessItem(test_data1)
        assert item.id == 12
        assert item.title1 == "haha"

        with pytest.raises(ReadOnlyException):
            item.dict_in_dict["123"]["1"] = 1

        with pytest.raises(AttributeError):
            item.list_in_list[0].append("1212")

    def test_pickle(self):
        l1 = ReadOnlyList([1, 2, 3])
        l2: List[int] = pickle.loads(pickle.dumps(l1, protocol=pickle.HIGHEST_PROTOCOL))
        assert l1 == l2

        d1 = ReadOnlyDict({1: 1, 2: 2, 3: 3})
        d2: Dict[int, int] = pickle.loads(
            pickle.dumps(d1, protocol=pickle.HIGHEST_PROTOCOL)
        )
        assert d1 == d2

        s1 = ReadOnlySet({3, 2, 1})
        s2: Set[int] = pickle.loads(pickle.dumps(s1, protocol=pickle.HIGHEST_PROTOCOL))
        assert s1 == s2
