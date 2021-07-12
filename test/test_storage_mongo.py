import asyncio
from koala.storage.storage_mongo import StorageMongo
import pytest
import pytest_asyncio.plugin
from koala.storage.storage import *
from koala.storage.record import *
from koala.storage.record_meta import *
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorCollection, AsyncIOMotorCursor


@record_meta("test_table", "uid")
class TestRecord(Record):
    uid: int
    name: str


@record_meta("test_table2", "unique_id", "pid")
class TestRecord2(Record):
    unique_id: str
    pid: str
    name: str


_connection_str = "mongodb://koala:123456@127.0.0.1:27017/koala_db"
_db_name = "koala_db"


def test_meta_data():
    meta_1 = get_record_meta(TestRecord)
    meta_2 = get_record_meta(TestRecord2)

    assert meta_1

    assert meta_1.table_name == "test_table"
    assert meta_1.key_info.key_name == "uid"
    assert meta_1.key_info.key_type == int
    assert meta_1.key_info.key_name_2 is None
    assert meta_1.key_info.key_type_2 is None

    assert meta_2

    assert meta_2.table_name == "test_table2"
    assert meta_2.key_info.key_name == "unique_id"
    assert meta_2.key_info.key_type == str
    assert meta_2.key_info.key_name_2 == "pid"
    assert meta_2.key_info.key_type_2 == str


def test_1():
    a = TestRecord(uid="1", name="123456")
    # print(a.to_dict())
    assert True


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_mongo_find():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]
    cursor: AsyncIOMotorCursor = collection.find({'uid': {'$eq': 1}})
    for document in await cursor.to_list(length=1024):
        print(document)
    assert True


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_mongo_upsert():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]
    result = await collection.update_one({"uid": 11}, {'$set': {"uid": 11, "name": "121212345678"}}, upsert=True)
    print(result)
    assert True


@pytest.mark.run(order=1)
@pytest.mark.asyncio
async def test_mongo_delete():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]
    result = await collection.delete_many({"uid": 1})
    print(result)
    assert True


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


def pytest_sessionfinish(session, exitstatus):
    asyncio.get_event_loop().close()


async def test_storage_mongo_update():
    storage = StorageMongo()
    storage.init_storage(connection_str=_connection_str, db=_db_name)

    record_storage = storage.get_storage(TestRecord)

    record = TestRecord(uid=10, name="1010010")
    result = await record_storage.insert_one(record)
    print(result)
    pass


async def test_storage_mongo_delete():
    await asyncio.sleep(1)

    storage = StorageMongo()
    storage.init_storage(connection_str=_connection_str, db=_db_name)

    test_record = storage.get_storage(TestRecord)
    result = await test_record.delete_one(10)
    print(result)
    pass


async def test_storage_mongo_find():
    storage = StorageMongo()
    storage.init_storage(connection_str=_connection_str, db=_db_name)

    test_record = storage.get_storage(TestRecord)
    result = await test_record.find(1)
    print(result)
    pass


if __name__ == "__main__":
    loop = asyncio.get_event_loop()

    loop.run_until_complete(test_mongo_find())
    loop.run_until_complete(test_mongo_upsert())
    # loop.run_until_complete(test_mongo_delete())

    loop.run_until_complete(test_storage_mongo_find())
    loop.run_until_complete(test_storage_mongo_update())
    loop.run_until_complete(test_storage_mongo_delete())
