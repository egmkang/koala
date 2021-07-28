from koala.koala_config import get_config
from koala.placement.placement import *
from koala.pd.placement import *
from koala.server import server_base
import sample.player
import sample.account
from sample.account import *
import os


def run_server():
    get_config().parse(f"{os.getcwd()}/sample/app.yaml")
    set_placement_impl(PDPlacementImpl())

    server_base.init_server(globals().copy())
    server_base.register_user_handler(
        RequestAccountLogin, process_gateway_account_login)
    server_base.run_server()


run_server()
