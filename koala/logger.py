import sys
import copy
from koala.typing import *
from loguru import logger


FILE_FORMAT = "{time:HH:mm:ss.SSS} [{level: <5}] {module}:{line} {message}"


def init_logger(file_name_prefix: Optional[str],
                level: Optional[str],
                disable_console_log: Optional[bool] = None):
    if not level:
        level = "INFO"
    if disable_console_log:
        logger.remove(0)
    if file_name_prefix is not None:
        file_name_pattern = "%s_{time:YYYY-MM-DD_HH}.log" % file_name_prefix
        logger.add(sink=file_name_pattern, format=FILE_FORMAT,
                   rotation="1000 MB", encoding="utf-8", level=level)
        pass
