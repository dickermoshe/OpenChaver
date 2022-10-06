from pathlib import Path
import sys
import logging
from logging.handlers import TimedRotatingFileHandler
BASE_URL = "https://openchaver.com/"

# Check if app is being run from a frozen state
if getattr(sys, 'frozen', False):
    # Running in a bundle
    BASE_DIR = Path(sys._MEIPASS)
else:
    # Running live
    BASE_DIR = Path(__file__).parent

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

ch = logging.StreamHandler()
ch.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)

file_handler = TimedRotatingFileHandler(BASE_DIR / "openchaver.log",backupCount = 7, encoding="utf-8", delay=True, when="D")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)