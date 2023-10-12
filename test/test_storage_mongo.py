import asyncio
from koala.storage.storage_mongo import MongoDBConnection
import pytest
import pytest_asyncio.plugin
from koala.storage.storage import *
from koala.storage.record import *
from koala.storage.record_meta import *
from motor.motor_asyncio import (
    AsyncIOMotorClient,
    AsyncIOMotorCollection,
    AsyncIOMotorCursor,
)


@record_meta("test_table", "uid")
class RecordTestTable(Record):
    uid: int
    name: str


@record_meta("test_table2", "unique_id", "pid")
class RecordTestTable2(Record):
    unique_id: str
    pid: str
    name: str


_connection_str = "mongodb://root:tyhall51@172.16.40.210:8015/admin"
_db_name = "koala"


def test_meta_data():
    meta_1 = get_record_meta(RecordTestTable)
    meta_2 = get_record_meta(RecordTestTable2)

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


@pytest.mark.run(order=3)
@pytest.mark.asyncio
async def test_mongo_find():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]  # type: ignore
    cursor: AsyncIOMotorCursor = collection.find({"uid": {"$eq": 1}})  # type: ignore
    for document in await cursor.to_list(length=1024):
        print(document)
    assert True


@pytest.mark.run(order=2)
@pytest.mark.asyncio
async def test_mongo_upsert():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]  # type: ignore
    result = await collection.update_one(
        {"uid": 1}, {"$set": {"uid": 1, "name": "121212345678"}}, upsert=True
    )
    print(result)
    assert True


@pytest.mark.run(order=1)
@pytest.mark.asyncio
async def test_mongo_delete():
    _mongo_client = AsyncIOMotorClient(_connection_str)
    collection: AsyncIOMotorCollection = _mongo_client[_db_name]["test_table"]  # type: ignore
    result = await collection.delete_many({"uid": 1})
    print(result)
    assert True


@pytest.fixture
def event_loop():
    yield asyncio.get_event_loop()


def pytest_sessionfinish(session, exitstatus):
    asyncio.get_event_loop().close()


@pytest.mark.run(order=4)
@pytest.mark.asyncio
async def test_storage_mongo_update():
    connection = MongoDBConnection()
    connection.init(connection_str=_connection_str, db=_db_name)

    result = await connection.update(
        [
            RecordTestTable(uid=1, name="11111"),
            RecordTestTable(uid=2, name="2222"),
            RecordTestTable(uid=10001, name="22223"),
        ]
    )
    print(result)
    assert result


@pytest.mark.run(order=6)
@pytest.mark.asyncio
async def test_storage_mongo_delete():
    connection = MongoDBConnection()
    connection.init(connection_str=_connection_str, db=_db_name)

    result = await connection.delete(RecordTestTable, [1, 2])
    print(result)
    assert result


@pytest.mark.run(order=5)
@pytest.mark.asyncio
async def test_storage_mongo_find():
    connection = MongoDBConnection()
    connection.init(connection_str=_connection_str, db=_db_name)

    result = await connection.find(RecordTestTable, 10001)
    print(result)
    assert len(result) > 0

    result = await connection.find_one(RecordTestTable, 10001)
    print(result)
    assert result


async def main():
    await test_mongo_upsert()
    await test_mongo_find()
    await test_mongo_delete()

    await test_storage_mongo_update()
    await test_storage_mongo_find()
    await test_storage_mongo_delete()


if __name__ == "__main__":
    asyncio.run(main())
