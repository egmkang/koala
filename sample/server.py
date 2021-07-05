from koala.conf.loader import load_config
from koala.pd.api import set_pd_address
from koala.placement.placement import *
from koala.pd.placement import *
from koala.server import server_base
from koala.logger import init_logger
import sample.interfaces
import sample.player
from sample.account import *


_config = Config()


def init_server():
    set_pd_address(_config.pd_address)
    _pd_impl = PDPlacementImpl()
    init_logger(_config.log_name, _config.log_level)
    set_placement_impl(_pd_impl)

    server_base.init_server()
    server_base.register_user_handler(RequestAccountLogin, process_gateway_account_login)


def run_server():
    server_base.listen(_config.port, CODEC_RPC)
    server_base.run_server()


load_config()
init_server()
run_server()
