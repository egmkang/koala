CODEC_ECHO = 1      # 字节流编码, 需要自己在字节流编码上再做二次编解码
CODEC_RPC = 2       # KOLA RPC协议, 包头4字节`KOLA` magic number, 4字节Meta长度, 4字节Body长度, 均为小端
CODEC_GATEWAY = 3   #

CODEC_CUSTOM = 16   # 16 ~ 128为用户自行扩展的协议段
CODEC_MAX = 128

WINDOW_SIZE = 128 * 1024    # 滑动窗口大小

SOCKET_HEART_BEAT = 45    # Socket必须要45s内有消息上来, 否则会关掉链接
SOCKET_GC_INTERVAL = 5    # Socket检查链接超时的周期
