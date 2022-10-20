import logging
from logging.handlers import RotatingFileHandler

from .const import LOG_FILE

# Logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

file_handler = RotatingFileHandler(LOG_FILE, maxBytes=10 * 1000 * 1000, backupCount=5, encoding='utf-8')
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def handle_error(func):
    def __inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except:
            logger.exception(f"Exception in {func.__name__}")
            raise
    return __inner
