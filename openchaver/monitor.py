import logging
import threading as th

from .threads import *


# Logger
logger = logging.getLogger(__name__)


def run_monitor(die_event: th.Event|None = None):
    """
    Run the monitor
    """

    # Create events
    nsfw_take_event = th.Event()
    reporting_take_event = th.Event()
    idle_event = th.Event()

    # Define the screenshot services
    SERVICES = {
        # Detect idle
        "idle_detection": {
            "target": idle_detection,
            "args": (idle_event,),
            "kwargs": {"interval": 60, "reset_interval": 300},
            "daemon": True,
        },


        # Schedule random screenshots for the NSFW model
        "nsfw_random_scheduler": {
            "target": random_scheduler,
            "args": (nsfw_take_event,),
            "kwargs": {},
            "daemon": True,
        },
        # Schedule screenshots for the NSFW model based on usage
        "nsfw_usage_scheduler": {
            "target": usage_scheduler,
            "args": (nsfw_take_event,),
            "kwargs": {},
            "daemon": True,
        },
        # Take screenshots for the NSFW model
        "nsfw_screenshooter": {
            "target": screenshooter,
            "args": (
                nsfw_take_event,
                idle_event,
            ),
            "kwargs": {},
            "daemon": True,
        },

        # Schedule random screenshots for reporting
        "reporting_random_scheduler": {
            "target": random_scheduler,
            "args": (reporting_take_event,),
            "kwargs": dict(interval=[2700, 4500]),
            "daemon": True,
        },
        # Take screenshots for reporting
        "reporting_screenshooter": {
            "target": screenshooter,
            "args": (
                reporting_take_event,
                idle_event,
            ),
            "kwargs": dict(detect_nsfw=False),
            "daemon": True,
        },
        # Uploader
        "uploader": {
            "target": uploader,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },
        # Cleanup
        "cleanup": {
            "target": cleanup,
            "args": (),
            "kwargs": {},
            "daemon": True,
        },
    }

    thread_runner(SERVICES, die_event)

