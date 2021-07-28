import os
from koala.koala_config import get_config
from koala.placement.placement import *
from koala.pd.placement import *
from koala.server import server_base
from koala.server.fastapi import *
from sample.fastapi.http_api import *
import sample.player


def run_server():
    get_config().parse(f"{os.getcwd()}/sample/app.yaml")
    set_placement_impl(PDPlacementImpl())

    server_base.init_server(globals().copy())
    server_base.create_task(run_serve(host="0.0.0.0", port=8000))
    server_base.run_server()


run_server()
