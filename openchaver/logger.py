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