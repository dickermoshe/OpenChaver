import logging
import dataset
from random import randint
import time
from pathlib import Path
import threading as th
from queue import Queue
from pynput import mouse

try:
    from openchaver import image_database_path , image_database_url
    from window import WinWindow as Window
except:
    from . import image_database_path , image_database_url
    from .window import WinWindow as Window


logger = logging.getLogger(__name__)



def idle_detection(idle_event: th.Event, interval: int = 10,reset_interval:int=300):
    """
    Check if the user is idle
    If so send event to screenshot service to stop taking screenshots.
    Every 5 minutes reset the idle timer
    """
    
    while True:
        last_active = time.time()
        if time.time() - last_active > reset_interval:
            idle_event.clear()
        
        with mouse.Events() as events:
            if events.get(interval) is None:
                idle_event.set()
                logger.info(f"{idle_detection.__name__}: User is idle")
            else:
                idle_event.clear()
                last_active = time.time()
                logger.info(f"{idle_detection.__name__}: User is active")

def random_scheduler(event: th.Event, interval: int | list[int, int] = [60, 300]):
    """
    NSFW Random Screenshot Scheduler
    Sends events to the nsfw screenshot service at random intervals
    """
    while True:
        event.set()
        t = (
            randint(interval[0], interval[1])
            if isinstance(interval, list)
            else interval
        )
        time.sleep(t)


def usage_scheduler(
    event: th.Event,
):
    """
    NSFW Usage Screenshot Scheduler
    Sends events to the nsfw screenshot service when the user loads a new window,
    only uses a window whose title has been stable for at least 10 seconds.
    After 5 minutes the title is considered stable again.
    """
    old_title = None
    old_time = time.time()
    while True:
        try:
            if (
                time.time() - old_time > 300
            ):  # Reset after 5 minutes of the title not changing
                old_title = None

            old_title = Window.grab_screenshot(stable=10, invalid_title=old_title).title
            logger.info(f"{usage_scheduler.__name__}: Sending screenshot event")
            event.set()
            old_time = time.time()  # Reset the timer
        except:  # This is raised when the window title is not stable or the window is invalid ( Closed )
            time.sleep(5)


def nsfw_screenshooter(
    take_event: th.Event,
    idle_event: th.Event,
    interval: int = 10,
):
    """
    NSFW Screenshooter Service
    Shoot a screenshot when the event is set, and pass it to the storage service if it is NSFW
    """
    while True:
        take_event.wait()
        while idle_event.is_set():
            time.sleep(10)  # Wait until the user is not idle
        take_event.clear()
        try:
            logger.info(f"{nsfw_screenshooter.__name__}: Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()

            if window.nsfw:
                window.save_to_database()
                logger.info(
                    f"{nsfw_screenshooter.__name__}: Saving screenshot to database"
                )

            time.sleep(interval)  # Never take more than 1 screenshot every 10 seconds
            del window
        except:
            logger.exception(f"{nsfw_screenshooter.__name__}: Error")
            pass


def report_screenshooter():
    """
    Report Screenshooter Service
    Shoot a screenshot about every hour and pass it to the storage service
    """
    while True:
        try:
            logger.info(f"{report_screenshooter.__name__}: Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()
            logger.info(
                f"{report_screenshooter.__name__}: Saving screenshot to database"
            )
            window.save_to_database()
            time.sleep(randint(2700, 4500))
            del window
        except:
            logger.exception(f"{report_screenshooter.__name__}: Error")
            pass





def screenshot_upload_service():
    """
    Screenshot Upload Service
    """
    try:
        db = dataset.connect(image_database_url)
    except:
        # Delete the database file and try again
        image_database_path.unlink()
        db = dataset.connect(image_database_url)

    table = db["images"]
    while True:
        for row in table:
            id = row["id"]
            # Upload to OpenChaver

            # Delete from database
            table.delete(id=id)
            pass


def main():
    """
    Screenshot Service
    """
    screenshots_queue = Queue()
    take_event = th.Event()
    idle_event = th.Event()

    threads = {
        "idle_detection": {
            "target": idle_detection,
            "args": (idle_event,),
            "kwargs": {'interval': 60, 'reset_interval': 300},
            "daemon": True,
        },
        "random_scheduler": {
            "target": random_scheduler,
            "args": (take_event,),
            "kwargs": {},
            "daemon": True,
        },
        "usage_scheduler": {
            "target": usage_scheduler,
            "args": (take_event,),
            "kwargs": {},
            "daemon": True,
        },
        "nsfw_screenshooter": {
            "target": nsfw_screenshooter,
            "args": (take_event, idle_event, screenshots_queue),
            "kwargs": {},
            "daemon": True,
        },
        "report_screenshooter": {
            "target": report_screenshooter,
            "args": (screenshots_queue,),
            "kwargs": {},
            "daemon": True,
        },
    }

    for k in threads.keys():
        threads[k]["thread"] = th.Thread(
            target=threads[k]["target"],
            args=threads[k]["args"],
            kwargs=threads[k]["kwargs"],
            daemon=threads[k]["daemon"],
        )

    for k in threads.keys():
        threads[k]["thread"].start()

    try:
        while True:
            for k in threads.keys():
                if not threads[k]["thread"].is_alive():
                    logger.error(
                        'Thread "{}" is dead, restarting...'.format(threads[k]["target"].__name__)
                    )
                    threads[k]["thread"] = th.Thread(
                        target=threads[k]["target"],
                        args=threads[k]["args"],
                        kwargs=threads[k]["kwargs"],
                        daemon=threads[k]["daemon"],
                    )
                    threads[k]["thread"].start()
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
