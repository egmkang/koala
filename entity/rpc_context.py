from gevent.queue import Queue

_empty_context = None


class RpcContext(object):
    def __init__(self):
        self.host = ""
        self.request_id = 0
        self.queue = Queue()
        self.running = False

    def send_message(self, obj):
        self.queue.put(obj)

    @staticmethod
    def empty():
        global _empty_context
        if _empty_context is None:
            _empty_context = RpcContext()
            _empty_context.host = None
            _empty_context.request_id = None
        return _empty_context
