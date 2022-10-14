import logging
from random import randint
import time
import threading as th

from mss import ScreenShotError
from pynput import mouse

from .window import Window, NoWindowFound, UnstableWindow,WindowDestroyed
from .opennsfw import OpenNsfw
from .db import ScreenshotDB , ConfigurationDB



# Logger
logger = logging.getLogger(__name__)

# Idle Detection Thread
def idle_detection(idle_event: th.Event, interval: int = 60, reset_interval: int = 300):
    """
    This Thread will detect if the user is idle for a certain amount of time.
    If so, it will send an event to the screenshot service to stop taking screenshots.
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

# Scheduler Threads
def random_scheduler(event: th.Event, interval: int | list[int] = [60, 300]):
    """
    This Thread will send an event to the screenshot service every `interval` seconds.
    If `interval` is a list, it will send an event every random number of seconds between `interval[0]` and `interval[1]`
    """
    while True:
        event.set()
        logger.info(f"Sending screenshot event")
        t = (
            randint(interval[0], interval[1])
            if isinstance(interval, list)
            else interval
        ) # Time to wait before sending another event
        logger.info(f"Waiting {t} seconds")
        time.sleep(t)

def usage_scheduler(
    event: th.Event,
    reset_interval: int = 300,
    stable_time: int = 10,
):
    """
    This Thread will send an event to the screenshot service whenever a window opens and
    stays open for more than n seconds.
    Every `reset_interval` seconds reset the idle timer
    `stable_time` is the amount of time a window has to stay open before sending an event
    """
    old_title = None
    old_time = time.time()
    while True:
        try:
            # Reset after 2.5 minutes of the title not changing
            if time.time() - old_time > reset_interval:
                logger.info(f"Resetting usage timer")
                old_title = None

            # Get the title of the active window
            logger.info(f"Getting Active Window")
            logger.debug(f"Old title: {old_title}")
            old_title = Window.get_active_window(
                stable=stable_time, invalid_title=old_title
            ).title
            logger.debug(f"Active Window Title: {old_title}")

            logger.info(f"Sending screenshot event")
            event.set()

            old_time = time.time()  # Set the time to the current time

        except UnstableWindow as e:  # This is raised when the window title is not stable
            logger.info(f"Unstable window. Continuing...")

        except NoWindowFound as e:
            logger.info(f"No window found that matches your prefrences. Continuing...")
            old_title = e.current_title
            time.sleep(5)

# Screenshooter Service
def screenshooter(
    take_event: th.Event,
    idle_event: th.Event,
    interval: int = 10,
    detect_nsfw: bool = True,
):
    """
    This Thread will take screenshots whenevever it receives an event from the scheduler
    unless the user is idle.
    If `detect_nsfw` is True, it will also detect NSFW content in the screenshot.
    It will wait `interval` seconds between each screenshot
    """

    
    logger.info(f"Starting Screenshooter Service")
    logger.debug(f"Interval: {interval}")
    logger.debug(f"Detect: {detect_nsfw}")
    while True:
        if not ConfigurationDB().is_configured:
            logger.info("Configuration is not complete")
            time.sleep(5)
            continue
        else:
            break
    
    if detect_nsfw:
        opennsfw = OpenNsfw()
    else:
        opennsfw = None
    
    while True:

        # Wait fot take event to be set, and the user to not be idle
        take_event.wait()
        logger.info(f"Take event received")

        while idle_event.is_set():
            logger.info(f"User is idle. Waiting...")
            time.sleep(10)
            continue

        take_event.clear()

        try:
            logger.info(f"Getting Active Window")
            window = Window.get_active_window()
            logger.debug(f"Active Window Title: {window.title}")

            logger.info(f"Taking screenshot")
            window.take_screenshot()

            if detect_nsfw:
                logger.info(f"Running NSFW detection")
                window.run_detection(opennsfw=opennsfw) #
            
            if window.is_nsfw or detect_nsfw == False:
                logger.info(f"Obfuscating screenshot")
                logger.info(f"Saving screenshot to database")
                ScreenshotDB().save_window(window)

            del window
            time.sleep(interval)

        except WindowDestroyed:
            logger.info(f"Window destroyed. Continuing...")
            pass

        except ScreenShotError:
            logger.exception(f"MSS Error. Continuing...")
            pass

