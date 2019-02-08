_global_factory_dict = dict()


def entity_factory(entity_type: int):
    if entity_type in _global_factory_dict:
        raise Exception("entity_factory %s is exists" % entity_type)

    def factory(fn):
        _global_factory_dict[entity_type] = fn
        return fn
    return factory


def new_entity(entity_type: int, uid: int):
    global _global_factory_dict
    if entity_type not in _global_factory_dict:
        return None
    return _global_factory_dict[entity_type](uid)
