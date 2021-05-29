
class Buffer:
    def __init__(self):
        self._buffer = bytearray(1024)
        self._read = 0
        self._write = 0

    @staticmethod
    def from_bytes(array: bytes):
        buffer = Buffer()
        buffer._buffer = array
        buffer._write = len(array)
        return buffer

    def shrink(self):
        length = self.readable_length()
        if length > 0:
            self._buffer[0: length] = self._buffer[self._read: self._write]
        self._write = length
        self._read = 0

    def has_read(self, count: int):
        self._read += count

    def readable_length(self):
        return self._write - self._read

    def writeable_length(self):
        return len(self._buffer) - self._write

    def append(self, data: bytes):
        first_space = min(self.writeable_length(), len(data))
        second_space = len(data) - first_space
        self._buffer[self._write: self._write + first_space] = data[0: first_space]
        if second_space > 0:
            self._buffer.extend(data[first_space:])
        self._write += len(data)

    def slice(self, count=0):
        if count <= 0:
            return self._buffer[self._read: self._write]
        return self._buffer[self._read: self._read + count]

    def read(self, count):
        if count < 0:
            raise Exception("out of bound")

        array = self.slice(count)
        self._read += count
        return array
