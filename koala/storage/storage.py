from koala.koala_typing import *
from koala.storage.record import *
from koala.storage.record_meta import *


class IStorageConnection:
    @abstractmethod
    def init(self, **kwargs):
        pass

    @abstractmethod
    async def find(
        self,
        record_type: Type[RecordType],
        key1: TypeID,
        key2: Optional[TypeID] = None,
        length_limit: int = 1024,
    ) -> List[RecordType]:
        pass

    @abstractmethod
    async def find_one(
        self, record_type: Type[RecordType], key1: TypeID, key2: Optional[TypeID] = None
    ) -> RecordType | None:
        pass

    @abstractmethod
    async def update(self, update_records: List[RecordType]) -> int:
        pass

    @abstractmethod
    async def delete(
        self,
        record_type: Type[RecordType],
        keys: List[TypeID] | List[Tuple[TypeID, TypeID]],
    ) -> int:
        pass
