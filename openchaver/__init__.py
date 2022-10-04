from pathlib import Path
import logging
from logging.handlers import TimedRotatingFileHandler

BASE_DIR = Path(__file__).parent
image_database_path = BASE_DIR / "images.db"
image_database_url = "sqlite:///" + str(image_database_path)
config_path = BASE_DIR / "config.json"

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

# Make all new files readable by everyone (for Windows)


