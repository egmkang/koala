
_global_method = dict()


# entity type需要用户自己去规划
def rpc_method(entity_type: int = 0):
    global _global_method
    if entity_type not in _global_method:
        _global_method[entity_type] = dict()
    d = _global_method[entity_type]

    def method(fn):
        name = fn.__name__
        d[name] = fn
        # print("register %s, %s" % (entity_type, name))
        return fn
    return method


def get_rpc_method(entity_type: int, method_name: str):
    global _global_method
    if entity_type not in _global_method:
        return None
    d = _global_method[entity_type]
    if method_name not in d:
        return None
    return d[method_name]

