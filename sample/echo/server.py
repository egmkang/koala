from koala.server import server_base
import sample.player
import sample.account
from sample.account import *
import os


server_base.init_server(globals().copy(), f"{os.getcwd()}/sample/app.yaml")
server_base.use_pd()
server_base.register_user_handler(
    RequestAccountLogin, process_gateway_account_login)
server_base.run_server()
