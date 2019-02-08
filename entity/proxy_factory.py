_proxy_object_type = None


def register_proxy_object_type(class_):
    global _proxy_object_type
    _proxy_object_type = class_
    return class_


def new_proxy_object(*args):
    global _proxy_object_type
    return _proxy_object_type(*args)
