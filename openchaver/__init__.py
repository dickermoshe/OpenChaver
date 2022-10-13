from pathlib import Path
import os
import sys
import logging
from logging.handlers import TimedRotatingFileHandler

BASE_URL = "https://openchaver.com/"
API_BASE_URL = "https://api.openchaver.com/"


if not sys.executable.endswith(('python', 'python3','python.exe','python3.exe')):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).parent

if os.name == 'nt':
    DATA_DIR = Path(os.path.expandvars('%ProgramData%')) / 'OpenChaver'
    DATABASE_FILE = DATA_DIR / 'db.sqlite3'
    LOG_FILE = DATA_DIR / 'openchaver.log'
    if not DATA_DIR.exists():
        DATA_DIR.mkdir()
else:
    print('Unsupported OS')
    exit(1)

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

# Imports for Nuitka
import sqlalchemy.sql.default_comparator
import sqlalchemy.dialects.sqlite