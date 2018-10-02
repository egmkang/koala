from .singleton import Singleton

@Singleton
class ClassMethodCache:
    def __init__(self):
        self._dict = dict()
        pass

    def get_cls_method_set(self, _cls):
        if _cls not in self._dict:
            s = set([m for m in dir(_cls) if m.find('__') != 0])
            self._dict[_cls] = s
        return self._dict[_cls]

    def clear_class_method_set(self):
        self._dict.clear()


class MethodNotFoundException(Exception):
    def __init__(self):
        pass
