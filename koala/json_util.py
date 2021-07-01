import json

json_dumps = lambda o: json.dumps(o).encode()
json_loads = lambda b: json.loads(b.decode())

try:
    import orjson

    json_loads = orjson.loads
    json_dumps = orjson.dumps
except:
    pass
