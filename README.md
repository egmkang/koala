第一个版本是原型, 名字叫`Flash`, 实际上实现了俩版本, 一个asyncio的, 一个gevent的.

第二个版本正在写, 打算用asyncio, 因为目前asyncio的生态感觉还可以, 没必要继续在gevent上面怼了, 而且从Python 3.10开始, Python要大力度的提升性能, 计划在4个版本提升5倍性能, 所以也不需要那native plugin来做一些费力的活, 所以还是打算原生python来做.

顺便对网关和存档等做一下抽象, 看看这次能不能做的好一点.

依赖:
* loguru
* httpx
* pydantic