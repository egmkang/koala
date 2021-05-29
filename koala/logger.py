import sys
import copy
from koala.typing import *
from loguru import logger


CONSOLE_FORMAT = "<green>{time:HH:mm:ss.SSS}</green> [{level: <5}] <le>{module}:{line}</le> {message}"
FILE_FORMAT = "{time:HH:mm:ss.SSS} [{level: <5}] {module}:{line} {message}"


console_config = {
    "handlers": [
        dict(sink=sys.stdout, format=CONSOLE_FORMAT),
    ],
}


def init_logger(file_name_prefix: Optional[str], level: Optional[str]):
    if file_name_prefix is not None:
        file_name_pattern = "%s_{time}.log" % file_name_prefix
        file_config = copy.deepcopy(console_config)
        file_config["handlers"].clear()
        file_config["handlers"].append(dict(sink=file_name_pattern, format=FILE_FORMAT, rotation="1000 MB"))
        pass
    else:
        logger.configure(**console_config)
    if level is not None:
        logger.level(level)
