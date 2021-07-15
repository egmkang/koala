v0.4

该版本完成:

* 对Storage的抽象和Mongo的实现
* Actor提供定时器
* 集群内TcpClient重连
* Actor GC
* PD支持删除操作, 用来支持Host快速重启
* 客户端认证和重连做了基本的抽象


v0.3

该版本名字改名为`koala`.

该版本引入了`网关(Gateway)`和`PlacementDriver`这两个概念, 其中`Gateway`主要用来解决与客户端之间的通讯(第一个包和后续的包); `PlacementDriver`的概念源自`Spanner/TiDB`一脉, 因为分布式有状态服务器里面都会有`placement`这个概念, 只是具体的做法和策略选择不太一样.

v0.1里面placement就做在`客户端侧`, v0.3选择把placement做到服务端, 单独出来了一个服务.

为了使`koala`具容易和其他语言配合工作, 在通讯协议上选择了一些更容易移植的方案. 其中`PD`服务器的通讯是HTTP+JSON; `Gateway`服务器通讯协议选择了和`Koala`服务器的RPC协议兼容, 均是`JSON Meta` + `Binary Body`的方式.


v0.1 和 v0.2

第一个版本和第二个版本均为原型, 当时心血来潮花了两天做了第一个版本, 名字叫`Flash`(疯狂动物城里面的那个树懒).

![image info](pic/flash.jpg)

当时的想法是实现一个`VirtualActor`模式的原型, 用来解决分布式逻辑的编写. 这和例如TiDB等分布式服务器所需要处理的问题是截然不同的. `Flash`更着重于满足`scale-out`的同时, 尽量提升`编写逻辑代码的效率`, 使服务器内部对象与对象的通讯变得简单易用.

第二个版本和第一个版本没有本质上的不同, 无非是把asyncio替换成了gevent. 那个时候IDE等工具对asyncio支持不是很友好, 少写一个`await`可能需要大半天时间来排查. 所以当时才换成了gevent.

```python
# 1
proxy = RpcProxyObject(TestPlayer, ENTITY_TYPE_PLAYER, random.randint(1, 100), RpcContext.GetEmpty())
while True:
    try:
        # 2
        await proxy.say(s[0: random.randint(1, len(s))])
    except Exception as e:
        print(e)
```

`Flash`从一开始就使用了`Random Placement`这种策略, 以及支持`Virtual Actor Model`和`可重入性(Reentrancy)`.