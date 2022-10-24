import logging
import time
from ..logger import handle_error
from ..const import SERVICE_NAME
from ..utils import start_service_if_stopped

logger = logging.getLogger(__name__)


@handle_error
def run_watcher():
    """This function Keeps the OpenChaver Service running"""
    logger.info("Starting the OpenChaver Watcher")
    while True:
        start_service_if_stopped(SERVICE_NAME)
        time.sleep(10)
