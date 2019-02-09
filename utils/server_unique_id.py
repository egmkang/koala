import uuid

_server_unique_id = ""


def get_server_unique_id():
    global _server_unique_id
    if len(_server_unique_id) <= 0:
        _server_unique_id = str(uuid.uuid4())
    return _server_unique_id
