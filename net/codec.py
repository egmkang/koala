from abc import ABCMeta, abstractmethod
from utils.buffer import Buffer


class Codec(object):
    __metaclass__ = ABCMeta

    def __init__(self):
        pass

    # (buffer, conn) => object
    @abstractmethod
    def decode(self, buffer: Buffer, conn):
        pass

    # (msg, conn) => bytes
    @abstractmethod
    def encode(self, msg, conn) -> bytes:
        pass
