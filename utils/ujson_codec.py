import ujson


def codec_ujson_encode(obj) -> str:
    data = ujson.encode(obj)
    return data


def codec_ujson_decode(data: str, _type):
    obj = _type()
    d = ujson.decode(data)
    obj.__dict__.update(d)
    return obj

