import logging
from random import randint
from creep_app.models import Screenshot

from mss import mss
from mss.windows import MSS
from mss.exception import ScreenShotError
from profanity_check import predict
import psutil

from datetime import timedelta
from django.utils import timezone


from creep_app.brain import NudeNet, splice_images, skin_pixels
from creep_app.models import Screenshot, Alert

logger = logging.getLogger("service")


def is_profane(s: str):
    return predict([s])[0] == 1


def single_service(
    request,
    min_queue: int = 2,
    max_queue: int = 20,
    stable_window: int = 5,
    cpu_threshold: int = 50,
    batch_size: int = 10,
    max_tries: int = 30,
    min_alert_time: int = 300,
    min_alert_size: int = 2,
):
    """One Service that runs all the requsite services"""

    #: MSS client
    sct: MSS = mss()
    logger.debug("MSS client created")

    #: Brain instance
    brain = NudeNet()
    logger.debug("Brain instance created")

    title = None
    raw_screenshots = []

    while True:
        try:
            image, title, exec_name = Screenshot.grab_screenshot(
                sct, max_tries=max_tries, invalid_title=title,stable_window = stable_window
            )
            if image is None:
                raise ScreenShotError()
            
            logger.debug("Screenshot taken")
            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
        except ScreenShotError:
            logger.exception("MSS Error. Recreating MSS client...")
            sct: MSS = mss()
            logger.debug("MSS client re-created")
            continue
        except:
            logger.exception("Screenshot Error. Retrying...")
            continue

        # If the screenshot contains skin and splices into images
        # or
        # random 1/10 chance
        # or
        # Title is profane
        # Then >> Save the screenshot

        # Splice the image
        splices = splice_images(image)
        logger.debug(f'Image spliced. {len(splices)} splices found')

        # Check if the splices contains skin
        skin = skin_pixels(splices) if len(splices) else False
        logger.debug(f'Image contains skin: {skin}')

        # Check if the title is profane
        profane = is_profane(title)
        logger.debug(f'Title is profane: {profane}')

        # Random 1/10 chance if we should save the screenshot
        random = randint(1, 10) == 1
        logger.debug(f'Random Save Chance: {random}')
        
        add_to_queue = skin or profane or random
        logger.debug(f'Add to Queue: {add_to_queue}')

        if add_to_queue:
            raw_screenshots.append(
                dict(image=image, title=title, exec_name=exec_name, splices=splices)
            )

        logger.debug(f'Queue Size: {len(raw_screenshots)}')

        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
            logger.debug('Queue is empty. Continuing...')
            continue

        # Skip if the CPU is too high, unless the is a large queue
        if len(raw_screenshots) < max_queue and psutil.cpu_percent() > cpu_threshold:
            logger.info("CPU too high. Skipping...")
            continue

        # If the queue is too small, then continue
        if len(raw_screenshots) < min_queue:
            logger.info("Queue too small. Skipping...")
            continue

        logger.info("Processing queue")
        # Run detections on batches
        for raw_screenshot in raw_screenshots:
            logger.info("Running detections")
            if not len (raw_screenshot["splices"]):
                continue
            results = brain.detect(raw_screenshot["splices"],batch_size=batch_size)
            for result in results:
                keep = randint(1, 20) == 1
                logger.debug(f'Keep: {keep}')
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

        # Clear the raw screenshots
        raw_screenshots = []

        # # Check if there are any alerts to send
        # logger.info("Checking for alerts")
        # nsfw_screenshots = Screenshot.objects.filter(alerts__isnull=True, is_nsfw=True)
        # if nsfw_screenshots.count() > 0:
        #     groups = []
        #     sub_group = [nsfw_screenshots[0]]
        #     for s in nsfw_screenshots[1:]:
        #         if (s.created - sub_group[-1].created).seconds < min_alert_time:
        #             sub_group.append(s)
        #         else:
        #             groups.append(sub_group)
        #             sub_group = [s]
        #     groups.append(sub_group)

        #     for group in groups:
        #         if len(group) >= min_alert_size:
        #             alert = Alert.objects.create(screenshots=group)
        #             alert.send()

        # # Delete old screenshots
        # screenshots = Screenshot.objects.filter(keep=False, is_nsfw=False)
        # for s in screenshots:
        #     s.image.delete()
        #     s.delete()

        # # Delete all screenshots older than 3 days
        # screenshots = Screenshot.objects.filter(
        #     created__lt=timezone.now() - timedelta(days=3)
        # )
        # for s in screenshots:
        #     s.image.delete()
        #     s.delete()

        # # Delete all alerts older than 3 days
        # Alert.objects.filter(created__lt=timezone.now() - timedelta(days=3)).delete()
