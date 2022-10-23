from asyncio.log import logger
import logging
from logging.config import dictConfig

from .const import LOG_FILE

dictConfig({
    'version': 1,
    'formatters': {
        'default': {
            'format':
            '%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s',
        }
    },
    'handlers': {
        'wsgi': {
            'class': 'logging.StreamHandler',
            'stream': 'ext://flask.logging.wsgi_errors_stream',
            'formatter': 'default'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE,
            'formatter': 'default',
            'maxBytes': 1024 * 1024 * 10,
            'backupCount': 5,
            'encoding': 'utf8'
        },
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'default'
        },
    },
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    },
    'loggers': {
        'openchaver': {
            'level': 'DEBUG',
            'handlers': ['file', 'console'],
            'propagate': True
        }
}})

logger = logging.getLogger('openchaver')

def handle_error(func):

    def __inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logger.exception(f"Exception in {func.__name__}")
            raise

    return __inner
