from pathlib import Path
import sys
from .dirs import get_data_dir, get_config_dir, get_install_dir
from .utils import delete_old_logs, is_frozen
import os
import logging

logger = logging.getLogger(__name__)
os.environ['NO_PROXY'] = 'localhost'

# Process Info
BASE_EXE = Path(sys.executable)
TESTING = not is_frozen()
SERVICE_NAME = "OpenChaver Service (TESTING)" if TESTING else "OpenChaver Service"
WATCHER_NAME = "OpenChaver Watcher (TESTING)" if TESTING else "OpenChaver Watcher"


# Dirs
INSTALL_DIR = get_install_dir()
DATA_DIR = get_data_dir()
CONFIG_DIR = get_config_dir()

WATCHER_LOGS = INSTALL_DIR / "watcher.log"
SERVICE_LOGS = INSTALL_DIR / "service.log"

# Delete old logs
delete_old_logs(INSTALL_DIR,keep = [WATCHER_LOGS,SERVICE_LOGS])

# Commands
MIGRATE_ARGS = ["migrate"]    # Migrates the database
SERVICE_ARGS = ["runservice"] # Runs the main service in the service manager
WATCHER_ARGS = ["runwatcher"] # Runs the watcher service in the service manager
MONITOR_ARGS = ["runmonitor"] # Runs the monitor client in the user session

if TESTING:
    MIGRATE_ARGS = [str(INSTALL_DIR / 'manage.py')] + MIGRATE_ARGS
    SERVICE_ARGS = [str(INSTALL_DIR / 'manage.py')] + SERVICE_ARGS
    WATCHER_ARGS = [str(INSTALL_DIR / 'manage.py')] + WATCHER_ARGS
    MONITOR_ARGS = [str(INSTALL_DIR / 'manage.py')] + MONITOR_ARGS

MIGRATE_COMMAND = [str(BASE_EXE)] + MIGRATE_ARGS
SERVICE_COMMAND = [str(BASE_EXE)] + SERVICE_ARGS
WATCHER_COMMAND = [str(BASE_EXE)] + WATCHER_ARGS
MONITOR_COMMAND = [str(BASE_EXE)] + MONITOR_ARGS

PORT = 61313

# Log all variables to the service log
logger.info("BASE_EXE: %s", BASE_EXE)
logger.info("TESTING: %s", TESTING)
logger.info("SERVICE_NAME: %s", SERVICE_NAME)
logger.info("WATCHER_NAME: %s", WATCHER_NAME)
logger.info("INSTALL_DIR: %s", INSTALL_DIR)
logger.info("DATA_DIR: %s", DATA_DIR)
logger.info("CONFIG_DIR: %s", CONFIG_DIR)
logger.info("WATCHER_LOGS: %s", WATCHER_LOGS)
logger.info("SERVICE_LOGS: %s", SERVICE_LOGS)
logger.info("MIGRATE_ARGS: %s", MIGRATE_ARGS)
logger.info("SERVICE_ARGS: %s", SERVICE_ARGS)
logger.info("WATCHER_ARGS: %s", WATCHER_ARGS)
logger.info("MONITOR_ARGS: %s", MONITOR_ARGS)
logger.info("MIGRATE_COMMAND: %s", MIGRATE_COMMAND)
logger.info("SERVICE_COMMAND: %s", SERVICE_COMMAND)
logger.info("WATCHER_COMMAND: %s", WATCHER_COMMAND)
logger.info("MONITOR_COMMAND: %s", MONITOR_COMMAND)
logger.info("PORT: %s", PORT)




