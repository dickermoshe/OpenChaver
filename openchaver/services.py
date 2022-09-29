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
import json

try:
    from window import WinWindow as Window
except:
    from .window import WinWindow as Window

BASE_DIR = Path(__file__).parent
image_database_url = 'sqlite:///' + str(BASE_DIR / 'images.db')
chaver_configfile = BASE_DIR / 'chaver_config.json'


def random_scheduler(event: mp.Event,
                     interval: int | list[int, int] = [60, 300]):
    """
    Screenshot Scheduler
    Take a screenshot every `interval` seconds
    params:
        event: mp.Event
            The event to set
        interval: int | list[int,int]
            The interval to wait between setting the event, if a list is
            provided, a random number between the two numbers will be chosen.
    """
    while True:
        event.set()
        t = randint(interval[0], interval[1]) if isinstance(interval,
                                                            list) else interval
        time.sleep(t)


def usage_scheduler(event: mp.Event, interval: int | list[int, int] = 10):
    """
    Screenshot Scheduler
    Take a screenshot when the user loads a new window,
    wait `interval` seconds before taking another screenshot,
    only uses a window whose title has been stable for at least 10 seconds
    """
    old_title = None
    while True:
        try:
            old_title = Window.grab_screenshot(stable=10,
                                               invalid_title=old_title).title
            event.set()
        except:
            pass
        finally:
            t = randint(interval[0], interval[1]) if isinstance(
                interval, list) else interval
            time.sleep(t)


def screenshooter_service(event: mp.Event, nsfw_screenshot_queue: mp.Queue):
    """
    Screenshooter Service
    Shoot a screenshot when the event is set
    """
    while True:
        event.wait()
        event.clear()
        try:
            window = Window.grab_screenshot()
            window.run_detection()
            if window.nsfw:
                nsfw_screenshot_queue.put(window)
            del window
        except:
            pass


def screenshot_storage_service(nsfw_screenshot_queue: mp.Queue):
    """
    Screenshot Storage Service
    """
    # Every 10 seconds set the event
    db = dataset.connect(image_database_url)
    table = db['images']
    while True:
        window: Window = nsfw_screenshot_queue.get()

        png = cv.imencode('.png', window.image)[1].tobytes()
        
        table.insert(dict(
            exec_name=window.exec_name,
            title=window.title,
            nsfw=window.nsfw,
            image=png,
            timestamp=time.time(),
            alerted=False
        ))

        del window

def alert_service(minute_range: int = 5,detections: int = 3):
    """
    Screenshot Alert Service
    If there are more than `detections` detections in the last `minute_range` minutes
    send an alert
    """
    # Every 10 seconds set the event

    db = dataset.connect(image_database_url)
    table = db['images']
    while True:
        then = time.time() - (minute_range * 60)
        rows = table.find(timestamp=dict(gt=then),alerted=False)
        if len(rows) > detections:
            # Mark the rows as alerted
            for row in rows:
                row['alerted'] = True
                table.update(row, ['id'])
            
            # Send the alert
            emails = json.load(chaver_configfile)['emails']
            for email in emails:
                pass



        


def main():
    """
    Screenshot Service
    """
    take_event = mp.Event()
    filtered_screenshot_queue = mp.Queue()

    random_scheduler_process = mp.Process(target=random_scheduler,
                                          args=(take_event, ))
    usage_scheduler_process = mp.Process(target=usage_scheduler,
                                         args=(take_event, ))
    screenshooter_process = mp.Process(target=screenshooter_service,
                                       args=(take_event,
                                             filtered_screenshot_queue))
    screenshot_storage_process = mp.Process(target=screenshot_storage_service,
                                            args=(filtered_screenshot_queue, ))

    random_scheduler_process.start()
    usage_scheduler_process.start()
    screenshooter_process.start()
    screenshot_storage_process.start()

    # Print the process IDs
    print(f"Random Scheduler Process ID: {random_scheduler_process.pid}")
    print(f"Usage Scheduler Process ID: {usage_scheduler_process.pid}")
    print(f"Screenshooter Process ID: {screenshooter_process.pid}")
    print(f"Screenshot Storage Process ID: {screenshot_storage_process.pid}")

    random_scheduler_process.join()
    usage_scheduler_process.join()
    screenshooter_process.join()
    screenshot_storage_process.join()


if __name__ == "__main__":
    main()
