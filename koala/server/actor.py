from koala.koala_typing import *
from koala.server.actor_context import ActorContext


class Actor:
    @property
    def context(self) -> Optional[ActorContext]:
        pass

    @property
    def type_name(self) -> str:
        return ""

    @property
    def uid(self) -> ActorID:
        return 0
