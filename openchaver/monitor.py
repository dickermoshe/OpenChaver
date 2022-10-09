import os
import logging
from random import randint
import time
import threading as th
from pynput import mouse
from mss import ScreenShotError
import requests
import psutil

from . import BASE_URL
from .window import WinWindow as Window
from .window import UnstableWindow ,NoWindowFound,WindowDestroyed
from .nsfw import OpenNsfw
from .db import ImageDB, ConfigDB

logger = logging.getLogger(__name__)

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
    After 2.5 minutes the title is considered stable again.
    """
    old_title = None
    old_time = time.time()
    while True:
        try:
            # Reset after 2.5 minutes of the title not changing
            if time.time() - old_time > 150:
                logger.info(f"Resetting usage timer")
                old_title = None
            
            # Get the title of the active window
            logger.info(f"Getting Active Window")
            logger.debug(f"Old title: {old_title}")
            old_title = Window.get_active_window(stable=10, invalid_title=old_title).title
            logger.debug(f"Active Window Title: {old_title}")
            
            
            logger.info(f"Sending screenshot event")
            event.set()

            old_time = time.time()  # Set the time to the current time

        except UnstableWindow as e: # This is raised when the window title is not stable
            logger.info(f"Unstable window. Continuing...")
        
        except NoWindowFound as e: 
            logger.info(f"No window found that matches your prefrences. Continuing...")
            old_title = e.current_title
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

    opennsfw = OpenNsfw()
    db = ImageDB()
    while True:
        # Wait fot take event to be set, and the user to not be idle
        take_event.wait()
        while idle_event.is_set():
            time.sleep(10)
        take_event.clear()

        try:
            logger.info(f"Getting Active Window")
            window = Window.get_active_window()
            logger.debug(f"Active Window Title: {window.title}")

            logger.info(f"Taking screenshot")
            window.take_screenshot()

            logger.info(f"Running NSFW detection")
            window.run_detection(opennsfw=opennsfw)

            if window.nsfw:
                logger.info(f"Obfuscating screenshot")
                window.obfuscate()
                logger.info(f"Saving screenshot to database")
                db.save_window(window)
                
            del window
            time.sleep(interval)
        
        except WindowDestroyed:
            logger.info(f"Window destroyed. Continuing...")
            pass

        except ScreenShotError:
            logger.exception(f"MSS Error. Continuing...")
            pass
            


def report_screenshooter():
    """
    Report Screenshooter Service
    Shoot a screenshot about every hour and save it to the database
    """

    opennsfw = OpenNsfw()
    db = ImageDB()
    while True:
        try:
            logger.info(f"Getting Active Window")
            window = Window.get_active_window()
            logger.debug(f"Active Window Title: {window.title}")

            logger.info(f"Taking screenshot")
            window.take_screenshot()

            logger.info(f"Running NSFW detection")
            window.run_detection(opennsfw=opennsfw)

            logger.info(f"Obfuscating screenshot")
            window.obfuscate()

            logger.info(f"Saving screenshot to database")
            db.save_window(window)

            del window
            time.sleep(randint(2700, 4500)) # Wait between 45 and 75 minutes
        except WindowDestroyed:
            logger.info(f"Window destroyed. Continuing...")
            pass

        except ScreenShotError:
            logger.exception(f"MSS Error. Continuing...")
            pass

def screenshot_uploader(userid:str):
    """Uploads Screenshots"""
    db = ImageDB()
    while True:
        try:
            for window in db.pop_windows():
                r = requests.post(BASE_URL + '/api/v1/screenshots', json=window, headers={"Authorization": f"Bearer {userid}"})
                if r.status_code == 200:
                    db.delete_window(window['id'])
                    logger.info(f"Screenshot uploaded")
        except:
            logger.exception("Error uploading screenshot")
        time.sleep(30)


def monitor_service():
    """
    Main function
    """
    logger.info(f"Starting monitor service")

    # Connect to config database
    logger.info(f"Creating Config DB")
    db = ConfigDB()

    # User check 
    user = db.get_user()
    if user is None:
        logger.error(f"OpenChaver is not configured.")
        return
    else:
        logger.info(f"OpenChaver is configured.")
    
    # Kill the old monitor service
    old_pid = db.get_pid('monitor')
    logger.info(f"Old PID: {old_pid}")
    if old_pid is not None:
        try:
            process = psutil.Process(old_pid)
            if process.name().lower() in ['python.exe', 'python3.exe','openchaver.exe']:
                logger.info(f"Killing old monitor service")
                process.terminate()
        except psutil.NoSuchProcess:
            logger.info(f"Old process with pid {old_pid} not found")

    # Get the current threads PID and save it to the database
    pid = os.getpid()
    logger.info(f"PID: {pid}")
    db.save_pid("monitor",pid)
    
    # Create events
    take_event = th.Event()
    idle_event = th.Event()

    # Define the screenshot services
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
        "screenshot_uploader": {
            "target": screenshot_uploader,
            "args": (user['userid'],),
            "kwargs": {},
            "daemon": True,
        },
    }

    # Create threads and start them
    for k in threads.keys():
        threads[k]["thread"] = th.Thread(
            target=threads[k]["target"],
            args=threads[k]["args"],
            kwargs=threads[k]["kwargs"],
            daemon=threads[k]["daemon"],
        )

    for k in threads.keys():
        threads[k]["thread"].start()

    # Loop -> Restart threads if they die and sleep for 5 seconds
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
