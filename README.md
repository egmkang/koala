This is a simple distributed system just like `Virtual Actor` (orleans), but this one is very simple and something differences between orleans:

* using `Distributed locks` to location one Object(`actor` or something)
  
  i don't know how orleans location one object.....
* using `MySQL`/`RocksDb` to cache the object location (not finished yet)
   
  orleans using a DHT to cache the objects location, its hard to impl  
* using `pickle rpc` to communicate with each other server
   
  cannot replace rpc and message encoding right now, so cannot cross languages (just Python3.5+)
* using `gevent`
* lack of a lot things


This project is a Sample.