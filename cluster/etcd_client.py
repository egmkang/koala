import etcd3
from utils.singleton import Singleton
from contextlib import contextmanager


@Singleton
class EtcdClient:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.client = etcd3.client(host=self.host, port=self.port)

    def get_client(self) -> etcd3.Etcd3Client:
        return self.client

    @contextmanager
    def get(self) -> etcd3.Etcd3Client:
        try:
            yield self.client
        except:
            pass
        finally:
            pass
