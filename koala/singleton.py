

def Singleton(class_):
    _instances = {}

    def instance(*args, **kwargs) -> class_:
        if class_ not in _instances:
            _instances[class_] = class_(*args, **kwargs)
        return _instances[class_]
    return instance
