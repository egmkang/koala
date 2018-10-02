import asyncio
import sys
from utils.log import logger

loop = None

def get_loop():
    try:
        import uvloop
        asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    except Exception as e:
        logger.error("use uvloop fail: %s" % e)
        if sys.platform == 'win32':
            loop = asyncio.ProactorEventLoop()
            asyncio.set_event_loop(loop)
        pass
    finally:
        loop = asyncio.get_event_loop()
    return loop


