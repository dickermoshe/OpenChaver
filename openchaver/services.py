import logging
import threading as th
from .threads import server, uploader , thread_runner
logger = logging.getLogger(__name__)


def run_services(die_event: th.Event|None = None):
    """
    Run a list of services
    """
    SERVICES = {
        "server":{
            "target": server,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },
    }
    thread_runner(SERVICES, die_event)

