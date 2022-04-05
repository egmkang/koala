class KoalaErrorCode(object):
    def __init__(self, c: int, e: str):
        self.code = c
        self.message = e


ERROR_PD_NEW_SERVER = KoalaErrorCode(10001, "生成服务器ID失败")
ERROR_PD_REGISTER_SERVER = KoalaErrorCode(10002, "注册服务器失败")
ERROR_PD_KEEP_ALIVE = KoalaErrorCode(10003, "保持心跳失败")
ERROR_PD_KEEP_ALIVE_TIME_OUT = KoalaErrorCode(10004, "保持心跳超时, 自动退出")
