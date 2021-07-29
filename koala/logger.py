import logging
from koala.typing import *
from loguru import logger


class _InterceptHandler(logging.Handler):
    loglevel_mapping = {
        50: 'CRITICAL',
        40: 'ERROR',
        30: 'WARNING',
        20: 'INFO',
        10: 'DEBUG',
        0: 'NOTSET',
    }

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except AttributeError:
            level = self.loglevel_mapping[record.levelno]

        # Find caller from where originated the logging call
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        log = logger.bind(request_id='app')
        log.opt(
            depth=depth,
            exception=record.exc_info
        ).log(level,
              record.getMessage())


def hook_logging():
    handlers: List[logging.Handler] = [_InterceptHandler()]
    logging.basicConfig(handlers=handlers, level=20)
    for _log in ['uvicorn',
                 'uvicorn.access'
                 'uvicorn.error',
                 'fastapi',
                 'sqlalchemy',
                 'databases']:
        _logger = logging.getLogger(_log)
        _logger.handlers = handlers

    return logger.bind(request_id='app')


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

    hook_logging()
