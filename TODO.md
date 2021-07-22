TODO:

v0.6

* [ ] http gateway
* [ ] rpc meta info(去掉装饰器)
* [ ] pd mongo storage
* [ ] build script
* [ ] sample


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
