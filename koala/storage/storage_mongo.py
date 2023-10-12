from motor.motor_asyncio import AsyncIOMotorCursor
from koala.storage.storage import *
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import DeleteOne, UpdateOne


class MongoDBConnection(IStorageConnection):
    def __init__(self):
        self.connection_string = ""
        self.db_name = ""
        self.mongo: Optional[AsyncIOMotorClient] = None  # type: ignore
        self.record_table_cache: Dict[Type, Tuple[RecordMetaData, Any]] = {}

    def init(self, **kwargs):
        self.connection_string = kwargs.get("connection_str")
        self.db_name = kwargs.get("db")
        self.mongo = AsyncIOMotorClient(self.connection_string)

    def __get_filter(
        self,
        meta: RecordMetaData,
        record: Optional[dict],
        key1: Optional[TypeID] = None,
        key2: Optional[TypeID] = None,
    ) -> dict[str, Any]:
        key_info = meta.key_info

        mongo_filter = {}
        name_1 = key_info.key_name
        mongo_filter[name_1] = {"$eq": record.get(name_1) if record else key1}
        assert mongo_filter[name_1]

        if key_info.key_name_2:
            name_2 = key_info.key_name
            mongo_filter[name_2] = {"$eq": record.get(name_2) if record else key2}
            assert mongo_filter[name_2]
        return mongo_filter

    def __get_meta_info_and_table(
        self, record_type: Type[RecordType]
    ) -> Tuple[RecordMetaData, Any]:
        if record_type in self.record_table_cache:
            return self.record_table_cache[record_type]

        meta_info = get_record_meta(record_type)
        if not meta_info:
            raise Exception("cannot find %s's meta data" % record_type)
        if not self.mongo:
            raise Exception("mongo db not init")
        table = self.mongo[self.db_name][meta_info.table_name]

        self.record_table_cache[record_type] = (meta_info, table)
        return meta_info, table

    async def find(
        self,
        record_type: Type[RecordType],
        key1: TypeID,
        key2: Optional[TypeID] = None,
        length_limit: int = 1024,
    ) -> List[RecordType]:
        meta_info, table = self.__get_meta_info_and_table(record_type)

        result: List[RecordType] = []
        mongo_filter = self.__get_filter(meta_info, None, key1, key2)
        cursor: AsyncIOMotorCursor = table.find(mongo_filter)  # type: ignore
        for document in await cursor.to_list(length_limit):
            obj = record_type.model_validate(document)
            result.append(obj)
        return result

    async def find_one(
        self, record_type: Type[RecordType], key1: TypeID, key2: Optional[TypeID] = None
    ) -> RecordType | None:
        result = await self.find(record_type, key1, key2, 1)
        if result:
            return result[0]
        return None

    async def update(self, update_records: List[RecordType]) -> int:
        if not update_records:
            return 0

        record_type = type(update_records[0])
        meta_info, table = self.__get_meta_info_and_table(record_type)
        requests = []
        for record in update_records:
            content = record.model_dump()
            mongo_filter = self.__get_filter(meta_info, content)
            requests.append(UpdateOne(mongo_filter, {"$set": content}, upsert=True))
        result = await table.bulk_write(requests)
        return result.upserted_count

    async def delete(
        self,
        record_type: Type[RecordType],
        keys: List[TypeID] | List[Tuple[TypeID, TypeID]],
    ) -> int:
        if not keys:
            return 0
        meta_info, table = self.__get_meta_info_and_table(record_type)
        requests = []
        if isinstance(keys[0], tuple):
            for k1, k2 in cast(List[Tuple[TypeID, TypeID]], keys):
                mongo_filter = self.__get_filter(
                    meta_info, record=None, key1=k1, key2=k2
                )
                requests.append(DeleteOne(mongo_filter))
        else:
            for k1 in cast(List[TypeID], keys):
                mongo_filter = self.__get_filter(meta_info, record=None, key1=k1)
                requests.append(DeleteOne(mongo_filter))
        result = await table.bulk_write(requests)
        return result.deleted_count
