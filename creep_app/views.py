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
    stable_window: int = 5,
    min_queue: int = 2,
    max_queue: int = 20,
    cpu_threshold: int = 50,
) -> None:
    """This process will take screenshots and put them in a queue"""
    logger = logging.getLogger("screenshot")

    logger.info("Initializing Screenshot Process...")
    import django
    from mss import mss
    from mss.exception import ScreenShotError

    django.setup()
    from creep_app.models import Screenshot

    sct = mss()
    title = None
    raw_screenshots = []
    logger.info("Screenshot Process Initialized")

    while True:
        try:
            logger.info("Taking Screenshot...")
            logger.debug(f"Max tries: {max_tries}")
            logger.debug(f"Stable window: {stable_window}")
            image, title, exec_name = Screenshot.grab_screenshot(
                sct,
                max_tries=max_tries,
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

        # Random 1/10 chance if we should save the screenshot
        random = randint(1, 10) == 1
        logger.info(f"Random Save Chance: {random}")

        # If the image contains skin or the title is profane or the random chance is true, then save the screenshot

        if (skin or profane or random) and len(splices):
            logger.info(f"Add to List: True")
            raw_screenshots.append(
                dict(image=image, title=title, exec_name=exec_name, splices=splices)
            )
        else:
            logger.info(f"Add to List: False")

        logger.debug(f"Queue Size: {len(raw_screenshots)}")

        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
            logger.info("Queue is empty. Continuing...")
            continue

        # Skip if the CPU is too high, unless the is a large queue
        elif len(raw_screenshots) < max_queue and psutil.cpu_percent() > cpu_threshold:
            logger.info("CPU too high. Skipping...")
            continue

        # If the queue is too small, then continue
        elif len(raw_screenshots) < min_queue:
            logger.info("Queue too small. Skipping...")
            continue

        # Otherwise, send raw_screenshots to the queue
        else:
            logger.info("Sending to queue")
            queue.put(raw_screenshots)
            raw_screenshots = []


def detect_process(
    queue: multiprocessing.Queue,
    batch_size: int = 10,
):
    logger = logging.getLogger("detect")
    logger.info("Initializing Detect Process...")
    import django

    django.setup()
    from creep_app.models import Screenshot

    brain = NudeNet()
    logger.info("Detect Process Initialized")

    while True:
        logger.info("Waiting for queue...")
        try:
            raw_screenshots = queue.get(timeout=1)
            logger.info("Queue received")
        except:
            logger.exception("Queue Error. Retrying...")
            time.sleep(1)
            continue

        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
            logger.debug("Queue is empty. Continuing...")
            continue

        logger.info(f"Starting Detectionon {len(raw_screenshots)} images")
        for raw_screenshot in raw_screenshots:
            image = raw_screenshot["image"]
            title = raw_screenshot["title"]
            exec_name = raw_screenshot["exec_name"]
            splices = raw_screenshot["splices"]

            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
            logger.debug(f"Splices: {len(splices)}")
            
            if not len(splices):
                logger.info("No splices found. Skipping...")
                continue
            
            logger.info("Classifying...")
            classify_results = brain.classify(splices)
            logger.debug(f"Classify results: {classify_results}")
            if len([cr for cr in classify_results if cr["sexy"] > 0.5 or cr["porn"] > 0.5]) == 0 :
                logger.info("Screenshot is clean")
                continue
            
            logger.info("Screenshot is suspicious")
            logger.info('Running Detection...')
            results = brain.detect(raw_screenshot["splices"], batch_size=batch_size)
            logger.debug(f"Detection results: {results}")
            
            for result in results:
                keep = randint(1, 20) == 1
                logger.debug(f'NSFW: {result["is_nsfw"]}')
                if result["is_nsfw"] or keep:
                    logger.info("Saving To Database")
                    Screenshot.save_screenshot(
                        raw_screenshot["image"],
                        raw_screenshot["title"],
                        raw_screenshot["exec_name"],
                        is_nsfw=result["is_nsfw"],
                        keep=keep,
                    )
                    break


def alert_process():
    logger = logging.getLogger("alert")
    logger.info("Initializing Alert Process...")
    from creep_app.models import Screenshot, Alert
    logger.info("Alert Process Initialized")
    while True:
        # Get the last 5 minutes
        last_5_minutes = timezone.now() - timedelta(minutes=5)

        # Get the screenshots
        screenshots = Screenshot.objects.filter(
            created_at__gte=last_5_minutes, is_nsfw=True, alerted=False
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
    p3 = multiprocessing.Process(
        target=alert_process,
    )
    p1.daemon = True
    p2.daemon = True
    p3.daemon = True
    p1.start()
    p2.start()
    p3.start()
    p1.join()
    p2.join()
    p3.join()
