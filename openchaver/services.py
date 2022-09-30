"""
There are at least 3 different services
    1. Screenshot Scheduler - Send screenshot request events to the screenshot service
    2. Screenshooter - Listens for screenshot request events and takes screenshots, passing them to the next service
    3. Screenshot Storage - Listens for screenshots and stores them
"""
import multiprocessing as mp
import dataset
from random import randint
import time
import cv2 as cv
from pathlib import Path
import threading as th

try:
    from window import WinWindow as Window
except:
    from .window import WinWindow as Window

BASE_DIR = Path(__file__).parent
image_database  = BASE_DIR / 'images.db'
image_database_url = 'sqlite:///' + str(image_database)
openchaver_configfile = BASE_DIR / 'openchaver_config.json'


def random_scheduler(event: mp.Event,
                     interval: int | list[int, int] = [60, 300]):
    """
    NSFW Random Screenshot Scheduler
    Sends events to the nsfw screenshot service at random intervals
    """
    while True:
        event.set()
        t = randint(interval[0], interval[1]) if isinstance(interval,
                                                            list) else interval
        time.sleep(t)

def usage_scheduler(event: mp.Event,):
    """
    NSFW Usage Screenshot Scheduler
    Sends events to the nsfw screenshot service when the user loads a new window,
    only uses a window whose title has been stable for at least 10 seconds
    """
    old_title = None
    while True:
        try:
            old_title = Window.grab_screenshot(stable=10,
                                               invalid_title=old_title).title
            event.set()
        except:
            time.sleep(5)
            pass

def nsfw_screenshooter(event: mp.Event, screenshot_queue: mp.Queue, interval: int = 10):
    """
    NSFW Screenshooter Service
    Shoot a screenshot when the event is set, and pass it to the storage service if it is NSFW
    """
    while True:
        event.wait()
        event.clear()
        try:
            window = Window.grab_screenshot()
            window.run_detection()
            if window.nsfw:
                screenshot_queue.put(window)
            time.sleep(interval) # Never take more than 1 screenshot every 10 seconds
            del window
        except:
            pass

def report_screenshooter(screenshot_queue: mp.Queue):
    """
    Report Screenshooter Service
    Shoot a screenshot about every hour and pass it to the storage service
    """
    while True:
        try:
            window = Window.grab_screenshot()
            screenshot_queue.put(window)
            time.sleep(randint(2700, 4500))
            del window
        except:
            pass

def screenshot_storage_service(screenshot_queue: mp.Queue):
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
    
    table = db['images']
    while True:
        window: Window = screenshot_queue.get()
        table.insert(dict(
            exec_name=window.exec_name,
            title=window.title,
            nsfw=window.nsfw,
            image=window.image,
            timestamp=time.time(),
        ))
        del window

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
    table = db['images']
    while True:
        for row in table:
            # Upload to OpenChaver
            # Delete from database

            pass

def main():
    """
    Screenshot Service
    """
    take_event = mp.Event()
    screenshot_queue = mp.Queue()

    random_scheduler_thread = th.Thread(target=random_scheduler,
                                        args=(take_event, ),daemon=True)
    usage_scheduler_thread = th.Thread(target=usage_scheduler,
                                         args=(take_event, ),daemon=True)
                                         
    nsfw_screenshooter_process = mp.Process(target=nsfw_screenshooter,
                                       args=(take_event,
                                             screenshot_queue),daemon=True)
    
    report_screenshooter_process = mp.Process(target=report_screenshooter,
                                        args=(screenshot_queue,),daemon=True)
     
    screenshot_storage_thread = th.Thread(target=screenshot_storage_service,
                                        args=(screenshot_queue,),daemon=True)
     
    random_scheduler_thread.start()
    usage_scheduler_thread.start()
    nsfw_screenshooter_process.start()
    report_screenshooter_process.start()
    screenshot_storage_thread.start()
    
    random_scheduler_thread.join()
    usage_scheduler_thread.join()
    nsfw_screenshooter_process.join()
    report_screenshooter_process.join()
    screenshot_storage_thread.join()
                            

    # Print the process IDs
    print(f"NSFW Screenshooter Process ID: {nsfw_screenshooter_process.pid}")
    print(f"Report Screenshooter Process ID: {report_screenshooter_process.pid}")

if __name__ == "__main__":
    main()
