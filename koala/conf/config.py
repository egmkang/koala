import time
from typing import List, Dict
from koala.singleton import Singleton
from koala.local_ip import get_host_ip
from koala.server.rpc_meta import get_all_impl_types


def _get_registered_services() -> Dict[str, str]:
    all_types = get_all_impl_types()
    return {i[0]: i[1].__qualname__ for i in all_types}


class Config(Singleton):
    def __init__(self):
        super(Config, self).__init__()
        self._ip = ""
        self._port = 0
        self._services: Dict[str, str] = dict()
        self._desc = ""
        self._start_time = int(time.time() * 1000)
        self._ttl = 15
        self._log_file_name = "HOST"
        self._log_level = "DEBUG"
        self._pd_address = ""
        self._private_key = ""
        self._console_log = True
        pass

    def set_port(self, port: int):
        self._port = port

    @property
    def port(self) -> int:
        return self._port

    def set_services(self, services: List[str]):
        if services is not None and len(services) > 0:
            self._services.clear()
            all_types = _get_registered_services()
            for key in services:
                if key in all_types:
                    self._services[key] = all_types[key]

    @property
    def services(self) -> Dict[str, str]:
        if len(self._services) == 0:
            self._services = _get_registered_services()
        return self._services
        pass

    def set_desc(self, desc: str):
        self._desc = desc

    @property
    def desc(self) -> str:
        return self._desc

    @property
    def start_time(self) -> int:
        return self._start_time

    def set_ttl(self, ttl: int):
        self._ttl = ttl

    @property
    def ttl(self) -> int:
        if self._ttl == 0:
            self._ttl = 15
        return self._ttl

    def set_address(self, ip: str):
        if ip is not None and len(ip) > 0:
            self._ip = ip

    @property
    def address(self) -> str:
        if len(self._ip) > 0:
            return "%s:%d" % (self._ip, self._port)
        return "%s:%d" % (get_host_ip(), self._port)

    @property
    def log_level(self):
        return self._log_level

    def set_log_level(self, level: str):
        self._log_level = level

    @property
    def log_name(self) -> str:
        return self._log_file_name

    def set_log_name(self, name: str):
        self._log_file_name = name

    @property
    def pd_address(self) -> str:
        return self._pd_address

    def set_pd_address(self, address: str):
        self._pd_address = address

    def set_private_key(self, key: str):
        self._private_key = key

    @property
    def private_key(self) -> str:
        return self._private_key

    @property
    def console_log(self) -> bool:
        return self._console_log

    def disable_console_log(self):
        self._console_log = False
