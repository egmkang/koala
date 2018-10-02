import socket

_local_ip = ""

def GetHostIp(host=None, port=None):
    global _local_ip
    if len(_local_ip) > 4:
        return _local_ip

    if host == None: host = '8.8.8.8'
    if port == None: port = 80
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect((host, port))
        ip = s.getsockname()[0]
        _local_ip = ip
    finally:
        s.close()
    return _local_ip
