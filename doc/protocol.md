# Koala Protocol

这部分是`Koala`实现的细节, 系统之间具体如何通讯等等.

## Gateway

`Gateway`的输入目前只支持`ws/wss`协议, 其中`wss`需要在LB上配置HTTPS监听器, 准确的说Gateway不接收wss请求, 只接受ws请求.

后面Gateway会支持`QUIC`协议, 由于客户端现在还未普及, 所以暂时未实现.

### 首包

每个客户端链接连到Gateway上面来, 必须要发一个内容是`JSON`的字符串, 用来表明自己的身份以及后续的认证.

其中json必须包含的字段有: `open_id`, `server_id`, `timestamp`, `check_sum`, 可选包含的字段有`actor_type`和`actor_id`.

JSON字符串的校验, 是把json对象的属性按照key排序(剔除check_sum字段), 然后依次拼接成`key1value1key2value2....private_key`, 通过`SHA256`算法得到Hash值, 然后和check_sum字段的值比较. 具体实现可以参考`test/test_check_sum.py`.

包含`actor_type`和`actor_id`的首包, 会直接将后续消息转发给对应的Actor; 否则会到可以提供`IAccount`服务的Host上面做查询, 找到对应服务器的地址后, 再做转发.

Host不可用之后, Gateway会寻找新的Host服务器, 其中会有一段时间的不可用(Host 3次心跳的时间长度).

### 后续包

后续包的格式没有限制, 推荐用Binary格式来发送消息.

## PlacementDriver

PD主要用来提供服务发现和对象的定位.

其中`{PD_ADDRESS}`是PD服务器的地址, 例如`http://127.0.0.1:2379`; 请求和返回的对象都通过JSON来序列化.

为了方面描述, 下面都通过`pydantic`的写法表示请求和返回的对象.

错误信息比较特殊, 如果PD内部出错, 那么Http返回的状态码则为`错误码`, http返回的内容则为`error_msg`.

### 生成新的服务器ID

路径: `{PD_ADDRESS}/pd/api/v1/id/new_server_id`

请求对象:
```python
class RequestNewServerId(BaseModel):
    pass
```

返回对象: 
```python
class PDResponse(BaseModel):
    error_code: int = 0     # 错误码
    error_msg: str = ""     # 错误信息

class ResponseNewServerId(PDResponse):
    id: int = 0
```

### 批量生成序列号

可以一次生成多个序列号, 需要提供`{key}`和`step`. 其中`key`是序列号的名称, `step`是步长.

路径: `{PD_ADDRESS}/pd/api/v1/id/new_sequence/{key}/{step}`

请求对象:
```python
class RequestNewSequence(BaseModel):
    pass
```

返回对象:
```python
class ResponseNewSequence(PDResponse):
    id: int = 0
```

### 注册服务器

路径: `{PD_ADDRESS}/pd/api/v1/membership/register`

请求对象:
```python
class HostNodeInfo(BaseModel):
    server_id: int = 0              # 服务器唯一ID
    load: int = 0                   # 服务器负载, 0表示无负载
    start_time: int = 0             # 服务器启动UTC时间戳, 精确到秒
    ttl: int = 0                    # 多久不续约会被PD服务器认为已经死掉了
    address: str = ""               # 服务器的地址, 例如"127.0.0.1:5555"
    services: Dict[str, str]        # 该进程提供的服务, 例如{"IPlayer": "Player", "IAccount": "AccountImpl"}
    desc: str = ""                  # 描述信息
    labels: Dict[str, str]          # 服务器的标签, 暂时可以不填

class RequestRegisterServer(HostNodeInfo):
    pass
```

返回对象:
```python
class ResponseRegsiterServer(PDResponse):
    lease_id: int                   # 租约ID, 后续需要通过这个ID来不停的keep alive, 否则服务器会被T下线
```

### 删除服务器

一般来讲是不需要这个API的, 但是在调试的时候很可能快速的把服务器又拉起来, 所以把上一个服务器删掉, 可以更方便的满足调试需求. 线上服务器一般来讲是不需要手动删除服务器的, 让他自然过期即可.

路径: `{PD_ADDRESS}/pd/api/v1/membership/delete`

请求对象:
```python
class RequestDeleteServer(BaseModel):
    server_id: int = 0
    address: str = ""
```

返回对象:
```python
class ResponseDeleteServer(PDResponse):
    server_id: int = 0
```

### 服务器续约

注册服务器的时候填的`TTL`是服务器最大的存活时间, 那么需要用`TTL/3`这样的频率去不断的续约, 否则服务器有可能会被PD删掉.

服务器一旦多次续约失败, 就需要主动退出, 因为已经和集群失联. 在Koala中, 节点的生死由PD决定, PD内部通过etcd来实现, 可以保证强一致性.

路径: `{PD_ADDRESS}/pd/api/v1/membership/keep_alive`

请求对象:
```python
class RequestKeepAlive(BaseMode):
    server_id: int = 0
    lease_id: int = 0
    load: int = 0
```

返回对象:
```python
class HostNodeAddRemoveEvent(BaseMode):
    time: int = 0
    add: List[int] = []
    remove: List[int] = []

class ResponseKeepAlive(PDResponse:
    hosts: Dict[int, HostNodeInfo] = dict()
    events: List[HostNodeAddRemoveEvent] = list()
```

每次KeepAlive都会返回当前集群的整体状况, 以及最近增加删除的节点(有可能会重复发).

### 对象定位

查找某种对象所在的服务器位置信息.

路径: `{PD_ADDRESS}/pd/api/v1/placement/find_position`

请求对象:
```python
class RequestFindPosition(BaseMode):
    actor_type: str = ""            # Actor的接口类型(非实现类型), 例如IPlayer, 而不是AccountImpl
    actor_id: str = ""              # Actor的ID
    ttl: int = 0                    # 0是长期存在的Actor; 一场战斗这种易失的对象, 暂时支持还不是很好, 后面会支持
```

返回对象:
```python
class ResponseFindPosition(PDResponse):
    actor_type: str = ""
    actor_id: str = ""
    ttl: int = 0
    create_time: int = 0
    server_id: int = 0
    server_address: str = ""
```

## Host

`Koala RPC`设计的时候参考过BRPC, 不过做了一些改动, 主要是为了跨平台和语言. protobuf做为meta信息的序列化协议确实不错, 但是在python上太慢, 所以`Koala RPC`换成了JSON.


### Koala RPC

Koala RPC的包由`包头`, `Meta`和`Body`三部分组成

#### 包头

包头长度为12字节, 首先是4字节的`KOLA`标识符, 下来是4字节小端的Meta长度, 最后是4字节小端的Body长度.

如果一个包的meta是20字节, body是30字节, 那么整个包的长度是12 + 20 + 30字节.

#### Meta

Meta信息是一个JSON字符串. 由于`Koala RPC`上面不仅仅要用来传输RPC协议, 还要用来做Gateway和Host之间的通讯, 所以Meta信息需要能支持多种对象.

Meta的格式是, `1`字节`类型名`长度, 然后是`类型名`的UTF-8字符串, 下来才是对象的JSON序列化内容.

```python
class RequestHeartBeat(BaseMode):
    milli_seconds: int = 0

def encode(req: BaseMode) -> bytes:
    name = req.__class__.__qualname__
    json_data: bytes = cast(bytes, json_loads(req.model_dump()))
    return b"".join((int.to_bytes(len(name), 1, 'little'), name.encode(), json_data))
```

#### Body

Body是一个二进制的串, python中的bytes对象. 具体到Host与Host中的通讯, Body通常是`pickle`格式的RPC参数. 但是在Host和网关的通讯中, Body通常是Client输入的内容或者是要发送给Client的内容.
