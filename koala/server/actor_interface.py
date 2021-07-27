from abc import ABC
from koala.typing import *


class ActorInterface(ABC):
    pass


ActorInterfaceType = TypeVar("ActorInterfaceType", bound=ActorInterface)
