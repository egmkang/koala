

class Singleton(object):
    _instance = None

    def __new__(clz, *args, **kwargs):
        if not isinstance(clz._instance, clz):
            clz._instance = object.__new__(clz, *args, **kwargs)
        return clz._instance
