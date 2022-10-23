import logging

from .app import run_app
from ..utils import thread_runner
from .watchdog import keep_monitor_alive
from ..logger import handle_error

logger = logging.getLogger(__name__)


@handle_error
def run_service():
    services = {
        # Detect idle
        "idle_detection": {
            "target": run_app,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },
        # Keep Monitor alive
        "keep_alive": {
            "target": keep_monitor_alive,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },
    }
    logger.info(f"Services - {services}")
    thread_runner(services)
