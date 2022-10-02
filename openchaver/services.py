import logging
import dataset
from random import randint
import time
from pathlib import Path
import threading as th
from queue import Queue

try:
    from window import WinWindow as Window
    from watchdog import hello
except:
    from .window import WinWindow as Window
    from .watchdog import hello

BASE_DIR = Path(__file__).parent
image_database = BASE_DIR / "images.db"
image_database_url = "sqlite:///" + str(image_database)
openchaver_configfile = BASE_DIR / "openchaver_config.json"

logger = logging.getLogger(__name__)


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
        hello(BASE_DIR, random_scheduler.__name__)


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

        hello(BASE_DIR, usage_scheduler.__name__)


def nsfw_screenshooter(event: th.Event, screenshots_queue: Queue, interval: int = 10):
    """
    NSFW Screenshooter Service
    Shoot a screenshot when the event is set, and pass it to the storage service if it is NSFW
    """
    while True:
        event.wait()
        event.clear()
        try:
            logger.info(f"{nsfw_screenshooter.__name__}: Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()
            window.obfuscate_image()
            if window.nsfw:
                screenshots_queue.put(window)
                logger.info(f"{nsfw_screenshooter.__name__}: Sending screenshot to storage service")

            time.sleep(interval)  # Never take more than 1 screenshot every 10 seconds
            del window
        except:
            logger.exception(f"{nsfw_screenshooter.__name__}: Error")
            pass

        hello(BASE_DIR, nsfw_screenshooter.__name__)


def report_screenshooter(screenshots_queue: Queue):
    """
    Report Screenshooter Service
    Shoot a screenshot about every hour and pass it to the storage service
    """
    while True:
        try:
            logger.info(f"{report_screenshooter.__name__}: Taking screenshot")
            window = Window.grab_screenshot()
            window.run_detection()
            window.obfuscate_image()
            logger.info(f"{report_screenshooter.__name__}: Sending screenshot to storage service")
            screenshots_queue.put(window)
            time.sleep(randint(2700, 4500))
            del window
        except:
            logger.exception(f"{report_screenshooter.__name__}: Error")
            pass
        hello(BASE_DIR, report_screenshooter.__name__)


def screenshot_storage_service(screenshots_queue: Queue):
    """
    Screenshot Storage Service
    """
    # Every 10 seconds set the event
    try:
        db = dataset.connect(image_database_url)
    except:
        # Delete the database file and try again
        image_database.unlink()
        db = dataset.connect(image_database_url)

    table = db["images"]
    while True:
        screenshots = []
        while not screenshots_queue.empty():
            screenshots.append(screenshots_queue.get())
        for screenshot in screenshots:
            w = dict(
                exec_name=screenshot.exec_name,
                title=screenshot.title,
                nsfw=screenshot.nsfw,
                image=screenshot.image,
                timestamp=time.time(),
            )
            table.insert(w)
        del screenshots
        time.sleep(10)
        hello(BASE_DIR, screenshot_storage_service.__name__)


def screenshot_upload_service():
    """
    Screenshot Upload Service
    """
    try:
        db = dataset.connect(image_database_url)
    except:
        # Delete the database file and try again
        image_database.unlink()
        db = dataset.connect(image_database_url)
    
    table = db["images"]
    while True:
        for row in table:
            id = row["id"]
            # Upload to OpenChaver


            # Delete from database
            table.delete(id=id)
            pass

        hello(BASE_DIR, screenshot_upload_service.__name__)


def main():
    """
    Screenshot Service
    """
    screenshots_queue = Queue()
    take_event = th.Event()

    random_scheduler_thread = th.Thread(
        target=random_scheduler, args=(take_event,), daemon=True
    )
    usage_scheduler_thread = th.Thread(
        target=usage_scheduler, args=(take_event,), daemon=True
    )

    nsfw_screenshooter_thread = th.Thread(
        target=nsfw_screenshooter, args=(take_event, screenshots_queue), daemon=True
    )

    report_screenshooter_thread = th.Thread(
        target=report_screenshooter,
        args=(screenshots_queue,),
        daemon=True,
    )

    screenshot_storage_thread = th.Thread(
        target=screenshot_storage_service,
        args=(screenshots_queue,),
        daemon=True,
    )

    random_scheduler_thread.start()
    usage_scheduler_thread.start()
    nsfw_screenshooter_thread.start()
    report_screenshooter_thread.start()
    screenshot_storage_thread.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    main()
