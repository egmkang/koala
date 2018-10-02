import ujson


def CodecUjsonEncode(obj) -> str:
    data = ujson.encode(obj)
    return data

def CodeUjsonDecode(data: str, _type):
    obj = _type()
    d = ujson.decode(data)
    obj.__dict__.update(d)
    return obj

