import json
import urllib3
from koala.typing import *


http = urllib3.PoolManager()

ResultType = TypeVar("ResultType")


__PD_ADDRESS = "http://10.246.34.33:2379"
__PD_INTERNAL_ADDRESS = __PD_ADDRESS + "/pd/api/v1"

PD_VERSION_URL = __PD_INTERNAL_ADDRESS + "/version"

PD_ID_NEW_SERVER_URL = __PD_INTERNAL_ADDRESS + "/id/new_server_id"
PD_ID_NEW_SEQUENCE_URL = __PD_INTERNAL_ADDRESS + "/id/new_sequence/"
PD_MEMBERSHIP_REGISTER_URL = __PD_INTERNAL_ADDRESS + "/membership/register"
PD_MEMBERSHIP_KEEP_ALIVE_URL = __PD_INTERNAL_ADDRESS + "/membership/keep_alive"
PD_PLACEMENT_FIND_POSITION_URL = __PD_INTERNAL_ADDRESS + "/placement/find_position"
PD_PLACEMENT_NEW_TOKEN_URL = __PD_INTERNAL_ADDRESS + "/placement/new_token"

__header = {'content-type': 'application/json'}
__POST = "POST"
__GET = "GET"


#
# 请求和返回的定义
#


class PDResponse(object):
    def __init__(self):
        self.error_code = 0
        self.error_msg: str = ""
    pass


class VersionResponse(PDResponse):
    def __init__(self):
        super().__init__()
        self.version: str = ""
        pass


class NewIDResponse(PDResponse):
    def __init__(self):
        super().__init__()
        self.id = 0


class HostNodeInfo(object):
    def __init__(self):
        self.server_id = 0
        self.load = 0
        self.start_time = 0
        self.ttl = 0
        self.address = ""
        self.services: Dict[str, str] = dict()
        self.desc = ""


class RegisterNewServerRequest(HostNodeInfo):
    def __init__(self):
        super().__init__()
        pass
    pass


class RegisterNewServerResponse(PDResponse):
    def __init__(self):
        super().__init__()
        self.lease_id = 0
        pass


class KeepAliveServerRequest(object):
    def __init__(self):
        self.server_id = 0
        self.lease_id = 0
        self.load = 0
        pass


class HostNodeAddRemoveEvent(object):
    def __init__(self):
        self.time = 0
        self.add: List[int] = []
        self.remove: List[int] = []
        pass


class KeepAliveServerResponse(PDResponse):
    def __init__(self):
        super().__init__()
        self.hosts: Dict[int, HostNodeInfo] = dict()
        self.events: List[HostNodeAddRemoveEvent] = list()

    def rebuild(self):
        json_hosts: dict = self.hosts
        json_events: list = self.events
        self.hosts = dict()
        self.events = list()
        for key in json_hosts:
            host = HostNodeInfo()
            host.__dict__.update(json_hosts[key])
            self.hosts[host.server_id] = host
            pass
        for item in json_events:
            event = HostNodeAddRemoveEvent()
            event.__dict__.update(item)
            self.events.append(event)
            pass
        pass
    pass


class FindActorPositionRequest(object):
    def __init__(self):
        self.actor_type = ""
        self.actor_id = ""
        self.ttl = 0
        pass


class FindActorPositionResponse(PDResponse):
    def __init__(self):
        super().__init__()
        self.actor_type = ""
        self.actor_id = ""
        self.ttl = 0
        self.create_time = 0
        self.server_id = 0
        self.server_address = ""
        pass


def __format_result(code: int, body: bytes, t: Type[ResultType]) -> ResultType:
    obj: ResultType = t()
    if code == 200:
        d = json.loads(body.decode("utf-8"))
    else:
        d = dict()
        d["error_code"] = code
        d["error_msg"] = body.decode("utf-8")
    obj.__dict__.update(d)
    return obj


def __request(url: str, args: Optional[dict], method: str = __POST, header: dict = __header) -> (int, bytes):
    data = None
    if args is not None:
        data = json.dumps(args).encode("utf-8")
    req = http.request(method, url, body=data, headers=header)
    return req.status, req.data


def set_pd_address(address: str):
    global __PD_ADDRESS
    if address[-1] == '/':
        address = address[:-1]
    __PD_ADDRESS = address
    pass


def get_version() -> VersionResponse:
    code, body = __request(PD_VERSION_URL, None, __GET, {})
    return __format_result(code, body, VersionResponse)


def new_server_id() -> NewIDResponse:
    code, body = __request(PD_ID_NEW_SERVER_URL, None)
    return __format_result(code, body, NewIDResponse)


def new_sequence_id(key: str, step: int = 100) -> NewIDResponse:
    url = "%s/%s/%d" % (PD_ID_NEW_SEQUENCE_URL, key, step)
    code, body = __request(url, None)
    return __format_result(code, body, NewIDResponse)


def register_server(server_id: int, start_time: int, ttl: int, address: str, services: Dict[str, str], desc: str = "", load: int = 0) -> RegisterNewServerResponse:
    req = RegisterNewServerRequest()
    req.server_id = server_id
    req.start_time = start_time
    req.ttl = ttl
    req.address = address
    req.services = services
    req.desc = desc
    req.load = load

    code, body = __request(PD_MEMBERSHIP_REGISTER_URL, req.__dict__)
    return __format_result(code, body, RegisterNewServerResponse)


def keep_alive(server_id: int, lease_id: int, load: int) -> KeepAliveServerResponse:
    req = KeepAliveServerRequest()
    req.server_id = server_id
    req.lease_id = lease_id
    req.load = load

    code, body = __request(PD_MEMBERSHIP_KEEP_ALIVE_URL, req.__dict__)
    result = __format_result(code, body, KeepAliveServerResponse)
    result.rebuild()
    return result


def find_actor_position(actor_type: str, actor_id: str, ttl: int) -> FindActorPositionResponse:
    req = FindActorPositionRequest()
    req.actor_type = actor_type
    req.actor_id = actor_id
    req.ttl = ttl

    code, body = __request(PD_PLACEMENT_FIND_POSITION_URL, req.__dict__)
    return __format_result(code, body, FindActorPositionResponse)


if __name__ == "__main__":
    f1 = find_actor_position("ITest", "1", 0)
    print(f1)

    new_id = new_server_id()
    print(new_id)
    new_id = new_sequence_id("hello")
    print(new_id)

