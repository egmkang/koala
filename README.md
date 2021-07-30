### Koala是一个跨平台, 用于构建可扩展的分布式有状态服务框架

Koala是一个异构的服务器框架, 其中网关用C#编写, PlacementDriver服务器使用Golang编写, Framework主体使用Python.

Koala采用了asyncio, 将`async/await`语法引入到整个framework以及编程模型上. 可以帮助任何熟悉async/await协程的人, 轻松的写出可以横向扩展的, 高性能有状态服务.

Koala在Python Asyncio之上实现了`Virtual Actor模式`, 该模式由微软研究院开发出来, 最早使用在Orleans项目上. 所以Koala本身拥有很多Orleans的优点, 实现上略有不同.

## Actors

Koala Framework的核心是`Actor`. 一个`Actor`就是`Interface` + `Identity` + `State`. `Interface`定义了该Actor所能提供的能力, `Identity`则用于同类Actor之间做隔离. 同时Koala还提供了持久化状态存储的帮助类库, 可以满足不同粒度的持久化. 一个Actor可以实现一个或者多个`Interface`, 可以在内存中存储或者不存储状态, Koala在这方面提供了较强的组合能力.

Koala Framework大量使用`Python TypeHints`, Actor之间的通讯是`强类型`的RPC, 可以(在动态语言上)提供友好的编程体验.

Actor的生命周期由Runtime控制, 用户不需要手动控制Actor的资源释放. Koala提供了额外的控制Actor生命长短, Actor加载和卸载的接口, 方便用户做额外的控制. 一般来讲用户不需要关心Actor是否存在, 只需要通过`Interface`直接调用Actor; 用户也不需要关心Actor在哪个服务器上, PD会找一个负载相对较轻的服务器来放置Actor实例, 同时Placement的维持强一致性.

## FastAPI

Koala Framework通过集成FastAPI来提供HTTP API, 可以无缝的和其他系统集成. 同时FastAPI可以访问`Actor`系统, 来实现有状态服务.

FastAPI也使用asyncio和TypeHints, 可以提供比较一致的编程体验.

### Actor例子

有一个`IPlayer`接口, 有一个`echo`函数.

```python
class IPlayer(ActorInterface):
    @abstractmethod
    async def echo(self, hello: str) -> str:
        pass
```

然后`PlayerImpl`类实现了`IPlayer`接口, 这就是`IPlayer`对象真正执行的逻辑.
```python
class PlayerImpl(IPlayer, ActorBase):
    def __init__(self):
        super(PlayerImpl, self).__init__()

    async def echo(self, hello: str) -> str:
        return hello
```

这时候就可以去拿到`IPlayer`的proxy对象, 去异步的执行RPC.
```python
# 1
proxy = get_rpc_proxy(IPlayer, "1")
echo_response = await proxy.echo("111222")
print(echo_response)    # 这里就会打印111222

# 2
class XXXActor(XXXInterface, ActorBase):
    ...
    async def func(self):
        proxy = self.get_proxy(IPlayer, "2")
        echo_response = await proxy.echo("222111")        
        ...
```

`例1`里面, 就可以在一个外部系统直接去调用Koala Actor; `例2`则是在Actor与Actor之间调用, Koala和Orleans一样实现了RPC的`可重入`, 这在Koala里面是默认实现而且不能关闭的(Orleans里面有开关).


### HTTP例子

用HTTP API来实现一个Echo, 其中Http只是提供接口, Actor用来响应真正的请求.

```python
# Actor接口
class IPlayer(ActorInterface):
    @abstractmethod
    async def echo(self, msg: str) -> str:
        pass
    pass

# HTTP接口
@app.get("/")
def root():
    return "hello world"


@app.get("/echo/{msg}")
async def echo(msg: str):
    proxy = get_rpc_proxy(IPlayer, "1")
    result = await proxy.echo(msg)
    return result
```

例子中, echo请求都会发送给`IPlayer/1`这个对象, 实际操作中, 可以选择合适的ID分布, 以满足更高的并发度和分摊服务器压力.

## Koala Runtime

Koala Runtime使用`Python3 AsyncIO`编写, 可以在Windows/Linux/macOS上面方便的调试和运行.

由于Actor之间已经做了隔离, `Host`进程这时就可以理解为一个容器, 里面放着不同类型不同ID的Actor实例. Koala Framework处理了Actor的位置算法, 以及Actor之间的通讯, 以及检测和故障恢复. 所以用户在调试单进程Host的时候可以正常工作, 就可以方便将程序扩展到整个集群.

除此之外, Koala Runtime还提供WebSocket, 协议无关的网关. 用户只需要实现`首包`规范, 后续就可以在WebSocket上传输自定义协议, 而不需要关心网关的实现. 后续网关还会支持`QUIC协议`, 用来提供更低延迟的交互服务.


## 特点

### 分布式有状态

Actor作为可编程的最小粒度, 可以将状态存储在Actor内部. 对外只表现出来`Interface` + `Identity`, 对内则表现出来实现细节和`State`. 实现细节上甚至可以在有状态服务内实现一个无状态的Actor, 有非常大的灵活性.

### 持久化

Koala提供了Actor Storage的抽象, 提供了最多两列的存储接口, 即`(Key1, Optional<Key2>) => Object`. 用户可以像Orleans那样将整个State存储到一个对象里面, 这样只需要使用`Key1`即可; 也可以将整个`State`分割成多个存储对象, 将一个存储对象分割成多行, 可以自由的组合. 在某些领域, 单个State的尺寸可能会比较大, 只提供整个对象的读写性能可能会比较低, 所以Koala在这方面只是做一个`可选的`Storage抽象, 并没有在Actor内做成强制性的.

### Actor Timer

Koala没有提供Orleans的reminder, 但是提供编程必须的Timer. Actor的消息派发会执行Timer, 所以Timer和RPC一样也是顺序执行的, 同时Timer会进行补偿, 不会发生明显的时间偏移和误差累积.

### 强一致的Placement

Koala在设计之初就考虑了如何实现一个强一致性的Placement, 虽然整个Koala不是一个CP系统, 但是还是在这方面做了一些努力. Koala`PlacementDriver`服务器使用golang编写, 集成了`etcd embed`, 集群Membership和服务发现依赖etcd, 这方面的强一致的; `Placement`依赖于etcd的分布式锁和额外的持久化缓存. 整个集群内的Membership和Placement信息会不一致(会最终一致), 但是当服务不可用的时候Koala不会选择立即切换可能有故障的服务, 而是等待etcd续约失败, 同时在目标服务器上面也会二次检测`Placement`的正确性.

### Fault Tolerance

Koala设计之初就考虑了可扩展性. 当一个新的机器加入到集群内, 集群会迅速感知到新节点的存在, 然后会尝试着将新的任务调度给新的节点; 当一个节点离开集群(或是出现故障), 集群也会感知到, 然后将那个节点上的Actor移动到其他可用节点上重新激活. 集群会自动检测服务的存活性, 并且自动恢复故障.

### 异构系统

Koala Framework主体使用Python语言, Gateway使用C#, PlacementDriver使用golang. 虽然使用了3种语言, 但是服务器与服务器之间的通讯经过了设计, 可以跨语言和进程. 甚至可以对某个进程进行重新实现, 都是可以的, 只需要满足`Protocol`即可, 详情可以参考doc中对`Protocol`细节的描述.

### 跨平台

Koala Framework整体都可以在Windows/Linux/macOS上面`Debug`和`运行`. 用户可以方便的将集群运行在托管虚拟机, Docker, 或者物理机上.

## License

本项目采用[MIT许可证](LICENSE).

## 链接

* [Microsoft Research project home](http://research.microsoft.com/projects/orleans/)
* [Virtual Actor](https://www.microsoft.com/en-us/research/publication/orleans-distributed-virtual-actors-for-programmability-and-scalability)
* [TiKV PD](https://github.com/tikv/pd)
* [FastAPI](https://fastapi.tiangolo.com/)