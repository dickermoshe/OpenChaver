import logging
import dataset
from random import randint
import time
import threading as th
from pynput import mouse

try:
    from openchaver import image_database_path, image_database_url
    from window import WinWindow as Window
    from window import UnstableWindow
except:
    from . import image_database_path, image_database_url
    from .window import WinWindow as Window
    from .window import UnstableWindow
logger = logging.getLogger(__name__)

ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s -> %(funcName)s  %(levelname)s - %(message)s')
ch.setFormatter(formatter)
logger.addHandler(ch)


def idle_detection(idle_event: th.Event, interval: int = 60, reset_interval: int = 300):
    """
    Check if the user is idle every `interval` seconds
    If so send event to screenshot service to stop taking screenshots.
    Every `reset_interval` seconds reset the idle timer
    """

    while True:

        last_active = time.time()  # The last time the user was active

        # Reset `idle_event` if `reset_interval` seconds have passed since the last time the user was active
        if time.time() - last_active > reset_interval:
            logger.info(f"Resetting idle timer")
            idle_event.clear()

        with mouse.Events() as events:
            # Wait `interval` seconds for the user to be active
            if events.get(interval) is None:
                idle_event.set()
                logger.info(f"User is idle")
            else:
                idle_event.clear()
                last_active = time.time()
                logger.info(f"User is active")

        time.sleep(5)  # Wait 5 second to lower power consumption


def random_scheduler(event: th.Event, interval: int | list[int, int] = [60, 300]):
    """
    NSFW Random Screenshot Scheduler
    Sends events to the nsfw screenshot service at random intervals.
    `interval` can be a single integer or a list of two integers.
    If it is a list, the screenshot service will be called at a random interval between the two numbers.
    """
    while True:
        event.set()
        logger.info(f"Sending screenshot event")
        t = (
            randint(interval[0], interval[1])
            if isinstance(interval, list)
            else interval
        )
        logger.info(f"Waiting {t} seconds")
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
            # Reset after 5 minutes of the title not changing
            if time.time() - old_time > 300:
                old_title = None
            
            # Get the title of the active window
            old_title = Window.grab_screenshot(stable=10, invalid_title=old_title,take=False).title
            
           
            event.set()
            logger.info(f"Sending screenshot event")

            old_time = time.time()  # Reset the timer

        except UnstableWindow: # This is raised when the window title is not stable or the window is invalid ( Closed )
            logger.exception(f"Unstable window. Continuing...")
            time.sleep(5)
        except:
            logger.exception(f"Screenshot not taken | Screenshot not saved")
            time.sleep(5)


def nsfw_screenshooter(
    take_event: th.Event,
    idle_event: th.Event,
    interval: int = 10,
):
    """
    NSFW Screenshooter Service
    Shoot a screenshot when the event is set, and save it to the database
    Never take a screenshot if the user is idle
    Wait `interval` seconds between each screenshot
    """
    while True:
        # Wait fot take event to be set, and the user to not be idle
        take_event.wait()
        while idle_event.is_set():
            time.sleep(10)
        take_event.clear()

        try:
            logger.info(f"Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()

            if window.nsfw:
                window.save_to_database()
                logger.info(f"Saving screenshot to database")
            
            del window
            time.sleep(interval)
        except:
            logger.exception(f"Screenshot not taken | Screenshot not saved")
            pass


def report_screenshooter():
    """
    Report Screenshooter Service
    Shoot a screenshot about every hour and pass it to the storage service
    """
    while True:
        try:
            logger.info(f"Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()
            logger.info(f"Saving screenshot to database")
            window.save_to_database()
            del window
            time.sleep(randint(2700, 4500)) # Wait between 45 and 75 minutes
        except:
            logger.exception(f"Screenshot not taken | Screenshot not saved")
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
    take_event = th.Event()
    idle_event = th.Event()

    threads = {
        "idle_detection": {
            "target": idle_detection,
            "args": (idle_event,),
            "kwargs": {"interval": 60, "reset_interval": 300},
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
            "args": (take_event, idle_event,),
            "kwargs": {},
            "daemon": True,
        },
        "report_screenshooter": {
            "target": report_screenshooter,
            "args": (),
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

    # Restart threads if they die and sleep for 5 seconds
    try:
        while True:
            for k in threads.keys():
                if not threads[k]["thread"].is_alive():
                    logger.error(f'Thread "{threads[k]["target"].__name__}" is dead, restarting...')
                    threads[k]["thread"] = th.Thread(
                        target=threads[k]["target"],
                        args=threads[k]["args"],
                        kwargs=threads[k]["kwargs"],
                        daemon=threads[k]["daemon"],
                    )
                    threads[k]["thread"].start()
            time.sleep(5)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
