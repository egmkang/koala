_fn = None

def SetProxyFactory(f):
    global _fn
    if _fn is None:
        _fn = f

def NewProxyObject(*args):
    global _fn
    return _fn(*args)
