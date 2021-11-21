from abc import ABC, abstractmethod
from koala import json_util
import time
import yaml
from koala.typing import *
from koala import local_ip
from koala.server import rpc_meta


def _get_registered_services() -> Dict[str, str]:
    all_types = rpc_meta.get_all_impl_types()
    return {i[0]: i[1].__qualname__ for i in all_types}


class KoalaConfig(ABC):
    @property
    @abstractmethod
    def port(self) -> int:
        pass

    @property
    @abstractmethod
    def services(self) -> Dict[str, str]:
        pass

    @abstractmethod
    def parse(self, file_name: str):
        pass

    @property
    @abstractmethod
    def ttl(self) -> int:
        pass

    @property
    @abstractmethod
    def address(self) -> str:
        pass

    @property
    @abstractmethod
    def log_level(self) -> str:
        pass

    @property
    @abstractmethod
    def log_name(self) -> str:
        pass

    @property
    @abstractmethod
    def pd_address(self) -> str:
        pass

    @property
    @abstractmethod
    def private_key(self) -> str:
        pass

    @property
    @abstractmethod
    def console_log(self) -> bool:
        pass

    @property
    @abstractmethod
    def start_time(self) -> int:
        pass

    @property
    @abstractmethod
    def desc(self) -> str:
        pass

    @property
    @abstractmethod
    def pd_cache_size(self) -> int:
        pass

    @property
    @abstractmethod
    def fastapi_port(self) -> int:
        pass


class KoalaDefaultConfig(KoalaConfig):
    def __init__(self) -> None:
        super(KoalaDefaultConfig, self).__init__()
        self._ip = ""
        self._port = 0
        self._services: Dict[str, str] = dict()
        self._desc = ""
        self._start_time = int(time.time() * 1000)
        self._ttl = 15
        self._log_file_name = "host"
        self._log_level = "DEBUG"
        self._pd_address = ""
        self._private_key = ""
        self._console_log = True
        self._pd_cache_size = 10 * 10000
        self._fastapi_port = 0

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
        return "%s:%d" % (local_ip.get_host_ip(), self._port)

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

    @property
    def pd_cache_size(self) -> int:
        return self._pd_cache_size

    def set_pd_cache_size(self, size: int):
        self._pd_cache_size = size

    @property
    def fastapi_port(self) -> int:
        return self._fastapi_port

    def set_fastapi_port(self, port: int):
        self._fastapi_port = port

    @classmethod
    def _load_config(cls, file_name: str) -> dict:
        return cls._load_as_json(file_name)

    @classmethod
    def _load_as_json(cls, file_name: str) -> dict:
        with open(file_name) as file:
            data = file.read()
            if file_name.endswith(".yaml"):
                yaml_config = yaml.full_load(data)
                return yaml_config
            if file_name.endswith(".json"):
                json_config = json_util.json_loads(data)
                return json_config
        raise Exception("KoalaDefaultConfig only support yaml or json config")

    def parse(self, file_name: str):
        server_config = self._load_config(file_name)
        if "port" in server_config:
            self.set_port(int(server_config["port"]))
        else:
            print("需要配置port, 监听的端口")
            return
        if "ip" in server_config:
            self.set_address(server_config["ip"])
        if "ttl" in server_config:
            self.set_ttl(int(server_config["ttl"]))
        if "services" in server_config:
            self.set_services(server_config["services"])
        if "log_name" in server_config:
            self.set_log_name(server_config["log_name"])
        else:
            print("需要配置log_name, 日志名")
            return
        if "log_level" in server_config:
            self.set_log_level(server_config["log_level"])
        if "console_log" in server_config:
            enable = bool(server_config["console_log"])
            if not enable:
                self.disable_console_log()
        if "pd_address" in server_config:
            self.set_pd_address(server_config["pd_address"])
        if "private_key" in server_config:
            self.set_private_key(server_config["private_key"])
        if "pd_cache_size" in server_config:
            self.set_pd_cache_size(int(server_config["pd_cache_size"]))
        if "fastapi" in server_config:
            self.set_fastapi_port(int(server_config["fastapi"]))
        print(server_config)


ConfigType = TypeVar("ConfigType", bound=KoalaConfig)
_config: Optional[KoalaConfig] = None


def get_config() -> KoalaConfig:
    global _config
    if not _config:
        _config = KoalaDefaultConfig()
    return _config


def set_config_impl(config_type: Type[ConfigType]):
    global _config
    _config = config_type()
    pass
