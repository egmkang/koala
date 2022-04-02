TODO:

v0.8

* [ ] build.sh升级到.net 6
* [ ] python代码用black格式化
* [ ] 依赖升级
* [ ] type hint继续加强
* [ ] 杂项

v0.7

* [x] hotfix
* [x] ActorID int/str support
* [x] Gateway using DotNetty

v0.6

* [x] Gateway
  * [x] check sum toggle
* [x] Host
  * [x] fastapi
    * [x] config
    * [x] http api
    * [x] logger
    * [x] doc
  * [x] rpc meta info(去掉装饰器)
  * [x] config
    * [x] config support json
    * [x] pd cache size config
  * [x] update host Load info
* [x] PD
  * [x] cache TTL
  * [x] upgrade etcd embed
* [x] build script
  * [x] Windows
* [x] sample
  * [x] Actor
  * [x] HTTP


v0.5

* [x] Gateway
  * [x] WebSocketRateLimit
  * [x] Gateway Config
* [x] doc
  * [x] README
  * [x] roadmap
  * [x] desgin
  * [x] protocol
* [x] Python Host
  * [x] Config
  * [x] logger
  * [x] ReadOnlyObject
  * [x] PrivateKey
  * [x] PD Address


v0.4 

* [x] storage
* [x] Actor Timer
* [x] client reconnect
* [x] Actor GC
* [x] PD support host restart, remove specified server
* [x] cluster client reconnect


v0.3 Koala

* [x] naming
* [x] using PD
  * [x] PD Impl
  * [x] Single Node Cluster Impl
     * [x] Interfaces and Services
* [x] Koala Framework
  * [x] asyncio rewrite
  * [x] Gateway
* [x] Gateway Protocol 
  * [x] using RPC Protocol
* [x] Sample
    * [x] simple client


v0.2 Flash prototype

v0.1 Flash prototype

* [x] RPC
    * [x] rpc codec
        - [x] ujson
        - [x] pickle
    * [x] rpc client
        - [x] rpc proxy object
        - [ ] rpc retry policy
    * [x] rpc server
    * [x] rpc improvement
* [x] message dispatch
    - [x] message dispatch queue
    - [x] global dispatch
    - [x] player dispatch
* [x] logging
* [x] machine membership
* [x] entity balance
    * [x] load balance
    * [x] player position
* [x] simple bench
