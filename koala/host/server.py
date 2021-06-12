from koala.placement.placement import *
from koala.pd.placement import *
from koala.server import server_base
from koala.logger import init_logger

_config = Config()


def init_server():
    _pd_impl = PDPlacementImpl()
    init_logger(_config.log_name, _config.log_level)
    set_placement_impl(_pd_impl)
    server_base.init_server(_config.thread_count)


def run_server():
    server_base.listen_rpc(_config.port)
    server_base.run_server()

