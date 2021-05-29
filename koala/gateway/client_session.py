from abc import ABCMeta, abstractmethod
from typing import Tuple, Callable, Optional
from koala.singleton import Singleton


class IGatewayClientSession(metaclass=ABCMeta):
    def __init__(self):
        pass

    @abstractmethod
    def token(self) -> bytes:
        pass

    @abstractmethod
    def account(self) -> str:
        pass

    @abstractmethod
    def destination(self) -> Tuple[str, str]:
        pass

    @abstractmethod
    def change_destination(self, service_type: str, actor_id: str):
        pass


class DefaultGatewayClientSession(IGatewayClientSession):
    def __init__(self):
        super().__init__()
        self._token = b""
        self._account = ""
        self._service_type = ""
        self._actor_id = ""
        pass

    def set_token(self, data: bytes):
        self._token = data

    def token(self) -> bytes:
        return self._token

    def set_account(self, account: str):
        self._account = account

    def account(self) -> str:
        return self._account

    def destination(self) -> Tuple[str, str]:
        return self._service_type, self._actor_id

    def change_destination(self, service_type: str, actor_id: str):
        self._service_type = service_type
        self._actor_id = actor_id


class GatewayClientSessionFactory(Singleton):
    _fn:  Optional[Callable[[bytes], IGatewayClientSession]]

    def __init__(self):
        super(GatewayClientSessionFactory, self).__init__()

    def new_session(self, data: bytes) -> Optional[IGatewayClientSession]:
        if self._fn:
            return self._fn(data)
        return None

    def set_factory_method(self, fn: Callable[[bytes], IGatewayClientSession]):
        self._fn = fn
