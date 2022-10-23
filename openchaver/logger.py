import logging
from logging.config import dictConfig

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
