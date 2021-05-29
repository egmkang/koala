from koala.conf.config import Config
import yaml

_config = Config()
CONFIG_FILE = "./app.yaml"


def _load_config() -> dict:
    with open(CONFIG_FILE, 'r') as file:
        data = file.read()
        yaml_config = yaml.full_load(data)
        return yaml_config


def load_config():
    server_config = _load_config()
    if "port" in server_config:
        _config.set_port(int(server_config["port"]))
    else:
        print("需要配置port, 监听的端口")
        return
    if "gateway_port" in server_config:
        _config.set_gateway_port(int(server_config["gateway_port"]))
    if "ip" in server_config:
        _config.set_address(server_config["ip"])
    if "gateway_ip" in server_config:
        _config.set_gateway_address(server_config["gateway_ip"])
    if "ttl" in server_config:
        _config.set_ttl(int(server_config["ttl"]))
    if "services" in server_config:
        _config.set_services(server_config["services"])
    if "log_name" in server_config:
        _config.set_log_name(server_config["log_name"])
    else:
        print("需要配置log_name, 日志名")
        return
    if "log_level" in server_config:
        _config.set_log_level(server_config["log_level"])
    if "pd_address" in server_config:
        _config.set_pd_address(server_config["pd_address"])
    print(server_config)
    pass
