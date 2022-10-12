import logging
import threading as th

from .detect import *
from .models import Configuration


# Logger
logger = logging.getLogger(__name__)


def run_services():
    """
    Run all services
    """

    while True:
        config : Configuration  = Configuration.get_solo()  # type: ignore
        if not config.is_configurated:
            logger.info("Configuration is not complete")
            time.sleep(5)
            continue
        else:
            break

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
            "kwargs": {},
            "daemon": True,
        },
    }

    # Create threads and start them
    for k in SERVICES.keys():
        SERVICES[k]["thread"] = th.Thread(
            target=SERVICES[k]["target"],
            args=SERVICES[k]["args"],
            kwargs=SERVICES[k]["kwargs"],
            daemon=SERVICES[k]["daemon"],
        )

    # Start threads
    for k in SERVICES.keys():
        SERVICES[k]["thread"].start()

    # Loop -> Restart threads if they die and sleep for 5 seconds
    while True:
        for k in SERVICES.keys():
            if not SERVICES[k]["thread"].is_alive():
                logger.error(
                    f'Thread "{SERVICES[k]["target"].__name__}" is dead, restarting...'
                )
                SERVICES[k]["thread"] = th.Thread(
                    target=SERVICES[k]["target"],
                    args=SERVICES[k]["args"],
                    kwargs=SERVICES[k]["kwargs"],
                    daemon=SERVICES[k]["daemon"],
                )
                SERVICES[k]["thread"].start()
        time.sleep(5)

