import os
import sys
from fastapi import FastAPI
import uvicorn
from uvicorn.supervisors import ChangeReload
from koala.logger import logger
from koala.koala_typing import *


app = FastAPI()


async def fastapi_serve(*args, **kwargs):
    config = uvicorn.Config(app, **kwargs)
    server = uvicorn.Server(config=config)

    if (config.reload or config.workers > 1) and not isinstance(app, str):
        logger.error(
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
