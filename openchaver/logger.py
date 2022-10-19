import logging
from logging.handlers import TimedRotatingFileHandler

from .const import LOG_FILE

# Logger
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

file_handler = TimedRotatingFileHandler(LOG_FILE,backupCount = 7, encoding="utf-8", delay=True, when="D")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

def handle_exception(exc_type, exc_value, exc_traceback):
    import sys
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return
    logging.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))


def handle_error(func):
    import sys

    def __inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            exc_type, exc_value, exc_tb = sys.exc_info()
            handle_exception(exc_type, exc_value, exc_tb)
    return __inner
