# Koala

`koala`的设计目标是实现:

* virtual actor model
* persistence storage
* placement
* gateway


## Virtual Actor Model

该模式最早出现在[Orleans](https://www.microsoft.com/en-us/research/project/orleans-virtual-actors/)中.

`koala`在实现virtual actor模式的时候, 大部分任务通过Actor模式的`MailBox`来调度, 只有在RPC需要可重入的时候, 才会单独开启新的协程来执行.

Python 3.5开始支持`async/await`编程模式, 所以`koala`在v0.3版本开始切换到asyncio, 提供和Orleans类似的编程模型.

```python
async def hello(self, my_id: TypeID, times: int) -> str:
    proxy = self.get_proxy(IService1, my_id)
    return "hello world %d, reentrancy: %s" % (times, await proxy.reentrancy())
```

大量使用TypeHints, 上例中`proxy`对象具有`IService1`类型, 提供较好的编程体验.

## persistence storage

`Koala`在持久化方便面的做法和`Orleans`不太一样. Orleans的持久化状态会把所有的状态放到一个对象. 通常游戏服务的状态会比较大, 将整个对象去load/store成本会比较高. 所以`Koala`希望降低这方面的粒度.

当然这方面的尝试不一定是最佳实践, 后面会根据实际情况做出调整.

目前的想法是, 提供`Key => Object`和`(Key1, Key2) => Object`这两种模式, 最多允许两个列组成一个唯一索引来存储数据. 其中第一种可以理解为一个玩家只有一个对象, 第二种可以理解为一个玩家有多个对象, 比如道具等.

这两种模式统一一下就变成了`(Key1, Optional[Key2]]) => Object`, 第二个Key可以缺省, 然后`Koala`在这种抽象上提供了upsert/query/delete三种操作.

```python
@record_meta("test_table", "uid")
class RecordTestTable(Record):
    uid: int
    name: str

record_storage = factory.get_storage(RecordTestTable)

record = RecordTestTable(uid=10, name="1010010")
result = await record_storage.insert_one(record)
```

## placement

所有的有状态服务, 都会有placement或者类似的概念.

在传统的游戏服务器中, placement大部分都实现在CenterServer或者类似的概念中, 只有这样的中间节点才能感知到整个服务器内所有节点的信息, 所以只有他知道某个对象在什么地方.

`Orleans`和`Dapr`中, 都选择了DHT来做对象的定位. 这两者都用了客户端侧算法来实现定位, 即算法实现在framework内, framework能感知到算法实现的细节. Orleans对于membership的感知则是通过gossip协议来实现的(存疑, 不是非常确定); Dapr则是用`consul etcd`自己造了一个placement服务, 所有的节点连上placement服务, 不停的更新自己节点的信息, 然后就可以通过gRPC Stream收到(广播)其他节点信息变得的通知.

`Koala`的placement设计的时候, 参考过TiDB(毕竟有很多代码都是从PD服务器里面扒来的). 每个节点启动, 到PD服务器里面去注册, 注册成功后开始不断的续约. 续约的结果, 会告诉当前节点整个集群的状态. 但是定位的算法实现是在PD服务器内做的, 也就是说集群通过续约的结果只能感知到其他节点, 并不能自己决定哪个对象应该在哪个节点上.

`Koala` Placement的本质是一个带权重的随机算法(只不过有持久化缓存).

## gateway

`Orleans`缺失这部分功能, 他只是提供了`GrainClient`和`Observers`.

由于`Koala`整个框架都是私有实现, 所以在私有实现上添加一个`Gateway`就会变得非常轻松. 甚至还可以做到消息从Gateway1进来, 到了Host1, 然后Host2, 最后再冲Gateway1里面发给客户端.

`Gateway`和Host通讯的协议, 沿用了RPC协议.