import logging
from logging.config import dictConfig
logging.StreamHandler
from .const import LOG_FILE

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format':
            '%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s',  # noqa: E501
        }
    },
    'handlers': {
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'formatter': 'default',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'encoding': 'utf8',
            'delay': True
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
    },
    'loggers': {
        'openchaver': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            'propagate': True
        }
    }
})

logger = logging.getLogger('openchaver')


def handle_error(func):

    def __inner(*args, **kwargs):
        # Set the attribute to the function name
        __inner.__name__ = func.__name__

        try:
            return func(*args, **kwargs)
        except:  # noqa: E722
            logger.exception(f"Exception in {func.__name__}")
            raise

    return __inner
