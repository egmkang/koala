import os
from koala.server import server_base
from koala.server.fastapi import *
from sample.fastapi.http_api import *
import sample.player


server_base.init_server(globals().copy(), f"{os.getcwd()}/sample/app.yaml")
server_base.use_pd()
server_base.listen_fastapi()
server_base.run_server()
