_fn = None


def set_proxy_factory(f):
    global _fn
    if _fn is None:
        _fn = f


def new_proxy_object(*args):
    global _fn
    return _fn(*args)
