import logging
import sys

LOGGING_CONFIG_DEFAULTS = dict(
    version=1,
    disable_existing_loggers=False,

    loggers={
        "root": {
            #"level": "DEBUG",
            "level": "INFO",
            "handlers": ["console"]
        },
    },
    handlers={
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "generic",
            "stream": sys.stdout
        },
        "access_console": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "stream": sys.stdout
        },
    },
    formatters={
        "generic": {
            "format": "[%(asctime)s.%(msecs)03d] [%(levelname)s] %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "class": "logging.Formatter"
        },
        "access": {
            "format": "[%(asctime)s.%(msecs)03d] - (%(name)s)[%(levelname)s][%(host)s]: " +
                      "%(request)s %(message)s %(status)d %(byte)d",
            "datefmt": "%Y-%m-%d %H:%M:%S",
            "class": "logging.Formatter"
        },
    }
)

logger = logging.getLogger("root")
access_log = logging.getLogger("access")
