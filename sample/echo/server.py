from koala.server import koala_host
import sample.player
import sample.account
from sample.account import *
import os


koala_host.init_server(globals().copy(), f"{os.getcwd()}/sample/app.yaml")
koala_host.use_pd()
koala_host.register_user_handler(
    RequestAccountLogin, process_gateway_account_login)
koala_host.run_server()
