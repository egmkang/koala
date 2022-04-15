from abc import ABC
from koala.koala_typing import *


class ActorInterface(ABC):
    pass


ActorInterfaceType = TypeVar("ActorInterfaceType", bound=ActorInterface)
