import asyncio
import time
import httpx
from pydantic import BaseModel
from koala.typing import *

ResultType = TypeVar("ResultType", bound='PDResponse')

__PD_ADDRESS = "http://127.0.0.1:2379"

PD_VERSION_URL = f"{__PD_ADDRESS}/pd/api/v1/version"
PD_ID_NEW_SERVER_URL = f"{__PD_ADDRESS}/pd/api/v1/id/new_server_id"
PD_ID_NEW_SEQUENCE_URL = f"{__PD_ADDRESS}/pd/api/v1/id/new_sequence"
PD_MEMBERSHIP_REGISTER_URL = f"{__PD_ADDRESS}/pd/api/v1/membership/register"
PD_MEMBERSHIP_DELETE_URL = f"{__PD_ADDRESS}/pd/api/v1/membership/delete"
PD_MEMBERSHIP_KEEP_ALIVE_URL = f"{__PD_ADDRESS}/pd/api/v1/membership/keep_alive"
PD_PLACEMENT_FIND_POSITION_URL = f"{__PD_ADDRESS}/pd/api/v1/placement/find_position"


#
# 请求和返回的定义
#


class PDResponse(BaseModel):
    error_code: int = 0
    error_msg: str = ""


class VersionResponse(PDResponse):
    version: str = ""


class NewServerIdResponse(PDResponse):
    id: int = 0


class NewSequenceIdResponse(PDResponse):
    id: int = 0


class HostNodeInfo(BaseModel):
    server_id: int = 0
    load: int = 0
    start_time: int = 0
    ttl: int = 0
    address: str = ""
    services: Dict[str, str]
    desc: str = ""


class RegisterNewServerRequest(HostNodeInfo):
    pass


class RegisterNewServerResponse(PDResponse):
    lease_id: int


class DeleteServerRequest(BaseModel):
    server_id: int = 0
    address: str = ""


class DeleteServerResponse(PDResponse):
    server_id: int = 0


class KeepAliveServerRequest(BaseModel):
    server_id: int = 0
    lease_id: int = 0
    load: int = 0


class HostNodeAddRemoveEvent(BaseModel):
    time: int = 0
    add: List[int] = []
    remove: List[int] = []


class KeepAliveServerResponse(PDResponse):
    hosts: Dict[int, HostNodeInfo] = dict()
    events: List[HostNodeAddRemoveEvent] = list()


class FindActorPositionRequest(BaseModel):
    actor_type: str = ""
    actor_id: str = ""
    ttl: int = 0


class FindActorPositionResponse(PDResponse):
    actor_type: str = ""
    actor_id: str = ""
    ttl: int = 0
    create_time: int = 0
    server_id: int = 0
    server_address: str = ""


def __format_result(code: int, body: bytes, result_type: Type[ResultType]) -> ResultType:
    if len(body) == 0:
        body = b'{}'
    if code == 200:
        return result_type.parse_raw(body.decode("utf-8"))
    else:
        obj = result_type()
        obj.error_code = code
        obj.error_msg = body.decode("utf-8")
        return obj


async def __request(url: str, args: Optional[dict]) -> Tuple[int, bytes]:
    if args is None:
        args = {}
    async with httpx.AsyncClient() as client:
        response = await client.post(url, json=args)
        return response.status_code, response.content


def set_pd_address(address: str):
    global __PD_ADDRESS
    global PD_VERSION_URL, PD_ID_NEW_SERVER_URL, PD_ID_NEW_SEQUENCE_URL, PD_MEMBERSHIP_REGISTER_URL, PD_MEMBERSHIP_DELETE_URL
    global PD_MEMBERSHIP_KEEP_ALIVE_URL, PD_PLACEMENT_FIND_POSITION_URL

    old_address = __PD_ADDRESS
    if address[-1] == '/':
        address = address[:-1]
    __PD_ADDRESS = address

    PD_VERSION_URL = PD_VERSION_URL.replace(old_address, __PD_ADDRESS)
    PD_ID_NEW_SERVER_URL = PD_ID_NEW_SERVER_URL.replace(
        old_address, __PD_ADDRESS)
    PD_ID_NEW_SEQUENCE_URL = PD_ID_NEW_SEQUENCE_URL.replace(
        old_address, __PD_ADDRESS)
    PD_MEMBERSHIP_REGISTER_URL = PD_MEMBERSHIP_REGISTER_URL.replace(
        old_address, __PD_ADDRESS)
    PD_MEMBERSHIP_DELETE_URL = PD_MEMBERSHIP_DELETE_URL.replace(
        old_address, __PD_ADDRESS)
    PD_MEMBERSHIP_KEEP_ALIVE_URL = PD_MEMBERSHIP_KEEP_ALIVE_URL.replace(
        old_address, __PD_ADDRESS)
    PD_PLACEMENT_FIND_POSITION_URL = PD_PLACEMENT_FIND_POSITION_URL.replace(
        old_address, __PD_ADDRESS)
    pass


async def get_version() -> VersionResponse:
    code, body = await __request(PD_VERSION_URL, None)
    return __format_result(code, body, VersionResponse)


async def new_server_id() -> NewServerIdResponse:
    code, body = await __request(PD_ID_NEW_SERVER_URL, None)
    return __format_result(code, body, NewServerIdResponse)


async def new_sequence_id(key: str, step: int = 512) -> NewSequenceIdResponse:
    url = "%s/%s/%d" % (PD_ID_NEW_SEQUENCE_URL, key, step)
    code, body = await __request(url, None)
    return __format_result(code, body, NewSequenceIdResponse)


async def register_server(server_id: int, start_time: int, ttl: int, address: str, services: Dict[str, str],
                          desc: str = "", load: int = 0) -> RegisterNewServerResponse:
    req = RegisterNewServerRequest(server_id=server_id,
                                   start_time=start_time,
                                   ttl=ttl,
                                   address=address,
                                   desc=desc,
                                   load=load,
                                   services=services)

    code, body = await __request(PD_MEMBERSHIP_REGISTER_URL, req.dict())
    return __format_result(code, body, RegisterNewServerResponse)


async def delete_server(server_id: int, address: str) -> DeleteServerResponse:
    req = DeleteServerRequest(server_id=server_id, address=address)

    code, body = await __request(PD_MEMBERSHIP_DELETE_URL, req.dict())
    return __format_result(code, body, DeleteServerResponse)


async def keep_alive(server_id: int, lease_id: int, load: int) -> KeepAliveServerResponse:
    req = KeepAliveServerRequest(
        server_id=server_id, load=load, lease_id=lease_id)

    code, body = await __request(PD_MEMBERSHIP_KEEP_ALIVE_URL, req.dict())
    result = __format_result(code, body, KeepAliveServerResponse)
    return result


async def find_actor_position(actor_type: str, actor_id: str, ttl: int) -> FindActorPositionResponse:
    req = FindActorPositionRequest(
        actor_type=actor_type, actor_id=actor_id, ttl=ttl)

    code, body = await __request(PD_PLACEMENT_FIND_POSITION_URL, req.dict())
    return __format_result(code, body, FindActorPositionResponse)


if __name__ == "__main__":
    async def main():
        server_id = await new_server_id()
        print(server_id.__class__, server_id)
        new_id = await new_sequence_id("hello")
        print(new_id.__class__, new_id)
        register_result = await register_server(server_id.id, int(time.time()), ttl=45, address="127.0.0.1:9999",
                                                services={'ITest': 'TestImpl'}, desc="debug server", load=1)
        print(register_result.__class__, register_result)
        await keep_alive(server_id.id, register_result.lease_id, 10)
        await asyncio.sleep(10)
        f1 = await find_actor_position("ITest", "1", 0)
        print(f1.__class__, f1)
        pass

    asyncio.run(main())
