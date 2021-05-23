import socket

_local_ip = ""


def get_host_ip(host=None, port=None):
    global _local_ip
    if len(_local_ip) > 4:
        return _local_ip

    if host is None:
        host = '8.8.8.8'
    if port is None:
        port = 80
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, port))
        ip = s.getsockname()[0]
        _local_ip = ip
    finally:
        s.close()
    return _local_ip
