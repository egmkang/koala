

def to_dict(obj) -> dict:
    if isinstance(obj, dict):
        return {k: to_dict(v) for k, v in obj.items()}
    elif hasattr(obj, "_ast"):
        return to_dict(obj._ast())
    elif hasattr(obj, "__dict__"):
        return {
            k: to_dict(v)
            for k, v in obj.__dict__.items()
            if not callable(v) and not k.startswith('_')
        }
    elif not isinstance(obj, str) and hasattr(obj, "__iter__"):
        return [to_dict(v) for v in obj]
    else:
        return obj
