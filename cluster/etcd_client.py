import aio_etcd as etcd
from contextlib import contextmanager
from utils.singleton import Singleton


@Singleton
class EtcdClient:
    def __init__(self, host=None, port=None):
        self.host = host
        self.port = port
        self.pool = list()

    @contextmanager
    def get(self):
        client = self._new_client()
        try:
            yield client
        except:
            pass
        finally:
            self._put(client)

    def _new_client(self):
        if len(self.pool) < 1:
            client = etcd.Client(host=self.host, port=self.port)
            return client
        return self.pool.pop()

    def _put(self, client):
        self.pool.append(client)

