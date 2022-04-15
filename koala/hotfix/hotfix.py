from abc import abstractmethod
from koala.koala_typing import *
from koala.server.actor_interface import ActorInterface
from koala.server.actor_base import ActorWithStrKey
from koala.logger import logger


class IHotFix(ActorInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def patch_code(self, code: str) -> Tuple[str, Optional[Exception]]:
        pass


class HotFix(IHotFix, ActorWithStrKey):
    def __init__(self):
        super().__init__()

    async def patch_code(self, code: str) -> Tuple[str, Optional[Exception]]:
        try:
            logger.info("patch_code, %s" % code)
            exec(code)
        except Exception as e:
            logger.exception(e)
            return ("fail", e)
        return ("success", None)
