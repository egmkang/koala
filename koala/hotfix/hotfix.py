from abc import abstractmethod
from koala.typing import *
from koala.server.actor_interface import ActorInterface
from koala.server.actor_base import ActorWithStrKey
from koala.logger import logger


class IHotFix(ActorInterface):
    def __init__(self) -> None:
        super().__init__()

    @abstractmethod
    async def patch_code(self, code: str) -> Tuple[str, Exception]:
        pass


class HotFix(IHotFix, ActorWithStrKey):
    def __init__(self):
        super().__init__()

    def patch_code(self, code: str) -> Tuple[str, Optional[Exception]]:
        try:
            logger.info("patch_code, %s" % code)
            exec(code)
            return ("success", None)
        except Exception as e:
            logger.exception(e)
            return ("fail", e)
