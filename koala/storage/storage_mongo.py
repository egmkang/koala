from os import name
from motor.motor_asyncio import AsyncIOMotorCollection, AsyncIOMotorCursor
from koala.storage.storage import *
from motor.motor_asyncio import AsyncIOMotorClient


class RecordStorageMongo(RecordStorage[RecordType]):
    def __init__(self, record_type: Type[RecordType], meta: RecordMetaData, db: AsyncIOMotorCollection):
        self.__record_type = record_type
        self.__meta = meta
        self.__db = db
        pass

    @property
    def table_name(self) -> str:
        return self.__meta.table_name

    @property
    def unique_key(self) -> KeyInfo:
        return self.__meta.key_info

    def __get_filter(self, record: Optional[dict], key: Optional[TypeID] = None, key2: Optional[TypeID] = None) -> dict:
        key_info = self.__meta.key_info

        mongo_filter = {}
        name_1 = key_info.key_name
        mongo_filter[name_1] = {'$eq': record.get(name_1) if record else key}
        assert mongo_filter[name_1]

        if key_info.key_name_2:
            name_2 = key_info.key_name
            mongo_filter[name_2] = {
                '$eq': record.get(name_2) if record else key}
            assert mongo_filter[name_2]
        return mongo_filter

    async def insert_one(self, record: RecordType) -> object:
        content = record.to_dict()
        mongo_filter = self.__get_filter(content)
        update = {"$set": content}
        result = await self.__db.update_one(mongo_filter, update, upsert=True)
        return result

    async def delete_one(self, key: TypeID, key2: Optional[TypeID] = None) -> object:
        mongo_filter = self.__get_filter(None, key, key2)
        result = await self.__db.delete_many(mongo_filter)
        return result

    async def find(self, key1: TypeID, key2: Optional[TypeID] = None) -> List[RecordType]:
        result: List[RecordType] = []
        mongo_filter = self.__get_filter(None, key1, key2)
        cursor: AsyncIOMotorCursor = self.__db.find(mongo_filter)
        for document in await cursor.to_list(1024):
            obj = self.__record_type.parse_obj(document)
            result.append(obj)
        return result

    async def find_one(self, key1: TypeID) -> Optional[RecordType]:
        document = await self.__db.find_one(self.__get_filter(None, key1))
        if document:
            obj = self.__record_type.parse_obj(document)
            return obj
        return None


class MongoStorageFactory(IStorageFactory):
    def __init__(self):
        self.connection_string = ""
        self.db_name = ""
        self.mongo: Optional[AsyncIOMotorClient] = None
        pass

    def init_factory(self, *args, **kwargs):
        self.connection_string = kwargs.get("connection_str")
        self.db_name = kwargs.get("db")
        self.mongo = AsyncIOMotorClient(self.connection_string)
        pass

    def get_storage(self, record_type: Type[RecordType]) -> RecordStorage[RecordType]:
        meta_info = get_record_meta(record_type)
        if not meta_info:
            raise Exception("cannot find %s's meta data" % record_type)
        if not self.mongo:
            raise Exception("mongo db not init")
        table = self.mongo[self.db_name][meta_info.table_name]
        obj = RecordStorageMongo(record_type, meta_info, table)
        return obj
