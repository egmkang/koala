import os
from koala.server import koala_host
from koala.server.fastapi import *
from sample.fastapi.http_api import *
import sample.player


koala_host.init_server(globals().copy(), f"{os.getcwd()}/sample/app.yaml")
koala_host.use_pd()
koala_host.listen_fastapi()
koala_host.run_server()
