from .app import app

from ..const import LOCAL_SERVER_PORT
from ..utils import thread_runner
from .watchdog import keep_alive
def run_service():
    SERVICES = {
        # Detect idle
        "idle_detection": {
            "target": app.run,
            "args": (),
            "kwargs": dict(port=LOCAL_SERVER_PORT),
            "daemon": True,
        },
        # Keep Monitor alive
        "keep_alive": {
            "target": keep_alive,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },

    }
    thread_runner(SERVICES)