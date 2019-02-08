import etcd3
from utils.singleton import Singleton

@Singleton
class EtcdHelper:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.client = etcd3.client(host=self.host, port=self.port)

    def get_client(self) -> etcd3.Etcd3Client:
        return self.client

    def get(self, path) -> bytes:
        value, _ = self.client.get(path)
        return value

    def get_prefix(self, path):
        return self.client.get_prefix(path)

    def put(self, path, value, ttl=60):
        self.client.put(path, value, self.client.lease(ttl=ttl))

    def get_lock(self, path, ttl=5):
        return self.client.lock(path, ttl)
