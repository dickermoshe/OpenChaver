
import logging
from random import randint
from creep_app.models import Screenshot

from mss import mss
from mss.windows import MSS
from mss.exception import ScreenShotError
from profanity_check import predict, predict_prob
import psutil

from datetime import timedelta
from django.utils import timezone


from creep_app.brain import Brain
from creep_app.models import Screenshot , Alert

logger = logging.getLogger('django')

def is_profane(s:str):
    return predict([s])[0] == 1

def single_service(
    request, min_queue:int = 10,max_queue: int = 20, cpu_threshold: int = 50, batch_size: int = 10, max_tries: int = 30, min_alert_time: int = 300,min_alert_size: int = 2
):
    """One Service that runs all the requsite services"""

    #: MSS client
    sct: MSS = mss()

    #: Brain instance
    brain = Brain()

    title = None
    raw_screenshots = []

    while True:
        # Try to take a screenshot of the active window
        try:
            logger.info("Taking screenshot")
            image, title, exec_name = Screenshot.grab_screenshot(sct, max_tries=max_tries, invalid_title=title)
            if image is None:
                raise ScreenShotError("Could not take screenshot")
        except ScreenShotError:
            logger.warning("MSS Error. Retrying...")
            sct: MSS = mss()
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
        splices = brain.splice(image)
        if (brain.skin_pixels(splices) or randint(1, 10) == 1 or is_profane(title)) and len(splices) > 0:
            logger.info("Adding screenshot to queue")
            splices = brain.match_size(splices)
            raw_screenshots.append(dict(image=image, title=title, exec_name=exec_name,splices=splices))
        
        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
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
            results = brain.detect(raw_screenshot['splices'])
            for result in results:
                keep = randint(1, 20) == 1
                if result['is_nsfw'] or keep:
                    logger.info("NSFW detected")
                    screenshot = Screenshot.save_screenshot(
                        raw_screenshot['image'],
                        raw_screenshot['title'],
                        raw_screenshot['exec_name'],
                        is_nsfw=True,
                        keep=keep,
                    )
                    break

        # Clear the raw screenshots
        raw_screenshots = []

        # Check if there are any alerts to send
        logger.info("Checking for alerts")
        nsfw_screenshots = Screenshot.objects.filter(alerts__isnull=True, is_nsfw=True)
        if nsfw_screenshots.count() > 0:
            groups = []
            sub_group = [nsfw_screenshots[0]]
            for s in nsfw_screenshots[1:]:
                if (s.created - sub_group[-1].created).seconds < min_alert_time:
                    sub_group.append(s)
                else:
                    groups.append(sub_group)
                    sub_group = [s]
            groups.append(sub_group)
        
            for group in groups:
                if len(group) >= min_alert_size :
                    alert = Alert.objects.create(screenshots = group)
                    alert.send()
        
        # Delete old screenshots
        screenshots = Screenshot.objects.filter(keep=False,is_nsfw=False)
        for s in screenshots:
            s.image.delete()
            s.delete()
        
        # Delete all screenshots older than 3 days
        screenshots = Screenshot.objects.filter(created__lt = timezone.now() - timedelta(days=3))
        for s in screenshots:
            s.image.delete()
            s.delete()

        # Delete all alerts older than 3 days
        Alert.objects.filter(created__lt = timezone.now() - timedelta(days=3)).delete()






                    
        
        



            


