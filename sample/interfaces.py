from abc import abstractmethod
from koala.server.actor_interface import ActorInterface


class IAccount(ActorInterface):
    pass


class IPlayer(ActorInterface):
    @abstractmethod
    async def echo(self, msg: str) -> str:
        pass
    pass
