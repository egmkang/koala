from koala.typing import *
from koala.koala_config import KoalaConfig, get_config, set_config_impl


class ConfigImpl(KoalaConfig):
    @property
    def port(self) -> int:
        return 0

    @property
    def services(self) -> Dict[str, str]:
        return {}

    def parse(self, file_name: str):
        pass

    @property
    def ttl(self) -> int:
        return 0

    @property
    def address(self) -> str:
        return ""

    @property
    def log_level(self) -> str:
        return "INFO"

    @property
    def log_name(self) -> str:
        return ""

    @property
    def pd_address(self) -> str:
        return ""

    @property
    def private_key(self) -> str:
        return ""

    @property
    def console_log(self) -> bool:
        return False

    @property
    def start_time(self) -> int:
        return 0

    @property
    def desc(self) -> str:
        return ""


def test_config_impl():
    set_config_impl(ConfigImpl)
    _config = get_config()
    assert _config.__class__ == ConfigImpl
