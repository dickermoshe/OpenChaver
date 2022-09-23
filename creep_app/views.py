import logging
from random import randint
import multiprocessing
import time

from profanity_check import predict
import psutil

from datetime import timedelta
from django.utils import timezone

from creep_app.brain import NudeNet, splice_images, skin_pixels


def is_profane(s: str):
    return predict([s])[0] == 1

def screenshot_process(
    queue: multiprocessing.Queue,
    max_tries: int = 30,
    stable_window: int = 7,
) -> None:
    """This process will take screenshots and put them in a queue"""
    logger = logging.getLogger("screenshot")

    logger.info("Initializing Screenshot Process...")
    import django
    from mss import mss
    from mss.exception import ScreenShotError

    django.setup()
    from creep_app.models import Screenshot
    from creep_app.brain import OpenNsfw

    sct = mss()
    opennsfw = OpenNsfw()
    title = None
    logger.info("Screenshot Process Initialized")

    while True:
        try:
            logger.info("Taking Screenshot...")
            logger.debug(f"Max tries: {max_tries}")
            logger.debug(f"Stable window: {stable_window}")
            image, title, exec_name = Screenshot.grab_screenshot(
                sct,
                max_tries=randint(5, max_tries),
                invalid_title=title,
                stable_window=stable_window,
            )
            if image is None:
                raise ScreenShotError()

            logger.info("Screenshot taken")
            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
        except ScreenShotError:
            logger.exception("MSS Error. Recreating MSS client...")
            sct = mss()
            logger.debug("MSS client re-created")
            continue
        except:
            logger.exception("Screenshot Error. Retrying...")
            continue

        # Splice the image
        splices = splice_images(image)
        logger.info(f"Image spliced. {len(splices)} splices found")

        # Check if the splices contains skin
        skin = skin_pixels(splices) if len(splices) else False
        logger.info(f"Image contains skin: {skin}")

        # Check if the title is profane
        profane = is_profane(title)
        logger.info(f"Title is profane: {profane}")


        # If the image contains skin or the title is profane, then save the screenshot
        if (skin or profane) and len(splices):
            filtered_splices = []
            
            for s in splices:
                if skin_pixels(s, threshold=0.1) and opennsfw.is_nsfw(s):
                    filtered_splices.append(s)

            if len(filtered_splices):
                queue.put(
                    dict(image=image, title=title, exec_name=exec_name, splices=filtered_splices)
                )
                logger.info("Add to List: True")

            else:
                logger.info(f"Add to List: False")
        else:
            logger.info(f"Add to List: False")
            
def detect_process(
    queue: multiprocessing.Queue,
):
    logger = logging.getLogger("detect")
    logger.info("Initializing Detect Process...")
    import django
    django.setup()
    from creep_app.models import Screenshot
    logger.info("Detect Process Initialized")
    raw_screenshots = []

    while True:
        # Add all the screenshots in the queue to the raw_screenshots list
        while not queue.empty():
            raw_screenshots.append(queue.get())
        
        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
            logger.debug("Queue is empty. Continuing...")
            time.sleep(5)
            continue
        
        brain = NudeNet()

        logger.info(f"Starting Detectionon {len(raw_screenshots)} images")
        for raw_screenshot in raw_screenshots:
            image = raw_screenshot["image"]
            title = raw_screenshot["title"]
            exec_name = raw_screenshot["exec_name"]
            splices = raw_screenshot["splices"]

            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
            logger.debug(f"Raw Splices: {len(splices)}")
            
            splices_sample = []
            for s in splices:
                if randint(1, 10) == 1:
                    splices_sample.append(s)
                elif skin_pixels(s, threshold=0.1):
                    splices_sample.append(s)

            logger.debug(f"Splices Sample: {len(splices_sample)}")
            splices = splices_sample

            if not len(splices):
                logger.info("No splices found. Skipping...")
                continue

            for splice in splices:
                detect_results = brain.detect([splice])[0]['is_nsfw']
                logger.info("Detection Complete")
                if detect_results:
                    logger.info("Saving To Database")
                    Screenshot.save_screenshot(
                        image,
                        title,
                        exec_name,
                        is_nsfw=detect_results,
                        keep=False,
                    )
                    logger.info("Saved To Database")
                    break
                else:
                    time.sleep(1)
            else:
                logger.info("No splices were NSFW. Skipping...")
                if randint(1, 20) == 1:
                    logger.info("Saving To Database")
                    Screenshot.save_screenshot(
                        image,
                        title,
                        exec_name,
                        is_nsfw=False,
                        keep=True,
                    )
                    logger.info("Saved To Database")
                else:
                    logger.info("Skipping Save")
        else:
            logger.info("Finished Detection")
            raw_screenshots = []
            del brain # Remove NudeNet from memory
            time.sleep(randint(5, 30))

def alert_process():
    logger = logging.getLogger("alert")
    logger.info("Initializing Alert Process...")
    import django
    django.setup()
    from creep_app.models import Screenshot, Alert
    logger.info("Alert Process Initialized")
    while True:
        # Get the last 5 minutes
        last_5_minutes = timezone.now() - timedelta(minutes=5)

        # Get the screenshots
        screenshots = Screenshot.objects.filter(
            created__gte=last_5_minutes, is_nsfw=True, alerted=False
        )

        # If there are 2 or more screenshots, then create an alert
        if len(screenshots) >= 2:
            logger.info("Creating Alert")
            Alert(screenshots=screenshots).save()
            for screenshot in screenshots:
                screenshot.alerted = True
                screenshot.save()

        # Send the alert
        Alert.send_alerts()

        time.sleep(30)


def single_service(request):
    """One Service that runs all the requsite services"""
    queue = multiprocessing.Queue()
    p1 = multiprocessing.Process(
        target=screenshot_process,
        args=(queue,),
    )
    p2 = multiprocessing.Process(
        target=detect_process,
        args=(queue,),
    )
    #p3 = multiprocessing.Process(
    #    target=alert_process,
    #)
    p1.daemon = True
    p2.daemon = True
    #p3.daemon = True
    p1.start()
    p2.start()
    #p3.start()
    p1.join()
    p2.join()
    #p3.join()
