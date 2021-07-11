from koala.storage.storage import *
from motor.motor_asyncio import *


class RecordStorageMongo(RecordStorage[RecordType]):
    def __init__(self, meta: RecordMetaData):
        self.__meta = meta
        pass

    @property
    def table_name(self) -> str:
        return self.__meta.table_name

    @property
    def unique_key(self) -> KeyInfo:
        return self.__meta.key_info

    async def insert_one(self, record: Record) -> bool:
        pass

    async def delete_one(self, record: Record) -> bool:
        pass

    async def find(self, key1: TypeID, key2: Optional[TypeID] = None) -> List[RecordType]:
        pass

    async def find_one(self, key1: TypeID) -> Optional[RecordType]:
        pass


class StorageMongo(IStorageEngine):
    def init_storage(self, *args, **kwargs):
        pass

    def get_storage(self, record_type: Type[RecordType]) -> RecordStorage[RecordType]:
        pass
