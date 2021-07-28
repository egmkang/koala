import os
import sys
from fastapi import FastAPI
from uvicorn import Server, Config
from uvicorn.supervisors import ChangeReload


app = FastAPI()


async def run_serve(*args, **kwargs):
    config = Config(app, **kwargs)
    server = Server(config=config)

    if (config.reload or config.workers > 1) and not isinstance(app, str):
        # TODO
        # logger
        print(
            "You must pass the application as an import string to enable 'reload' or "
            "'workers'."
        )
        sys.exit(1)

    if config.should_reload:
        sock = config.bind_socket()
        ChangeReload(config, target=server.run, sockets=[sock]).run()
    else:
        await server.serve()
    if config.uds:
        os.remove(config.uds)
