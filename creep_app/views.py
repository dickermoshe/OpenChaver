import logging
from random import randint
import multiprocessing
import time

from profanity_check import predict

from datetime import timedelta
from django.utils import timezone




def is_profane(s: str):
    return predict([s])[0] == 1


def screenshot_process(
    queue: multiprocessing.Queue,
    max_tries: int = 120,
    stable_window: int = 10,
    max_per_minute: int = 2,
) -> None:
    """
    This process will take screenshots and put them in a queue

    max_tries: The maximum number of tries to take a screenshot before taking one anyway
    stable_window: The number of tries that the screenshot must be stable for before taking one
    max_per_minute: The maximum number of screenshots to take per minute
    """
    # Logger
    logger = logging.getLogger("screenshot")

    # Imports
    logger.info("Initializing Screenshot Process...")
    import django

    django.setup()  # This is required for multiprocessing
    from mss import mss
    from mss.exception import ScreenShotError
    from creep_app.models import Screenshot
    from creep_app.brain import OpenNsfw, splice_images, skin_pixels, color_in_image

    # Create an MSS instance - This is used to take screenshots
    sct = mss()

    # Set the initial values
    title = None

    logger.info("Screenshot Process Initialized")
    logger.debug(f"Max tries: {max_tries}")
    logger.debug(f"Stable window: {stable_window}")

    # Loop forever
    max_screen_per_second = max_per_minute / 60 
    while True:
        # Take a screenshot of the active window
        start_time = time.time()
        try:
            
            logger.info("Taking Screenshot...")
            image, title, exec_name = Screenshot.grab_screenshot(
                sct,
                max_tries=randint(15, max_tries),
                invalid_title=title,
                stable_window=stable_window,
            )

            if image is None:
                logger.info("Screenshot is None. Restarting...")
                continue


            logger.info("Screenshot taken")
            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
        
        except ScreenShotError:
            logger.exception("MSS Error. Recreating MSS client...")
            sct = mss()
            logger.debug("MSS client re-created. Restarting...")
            continue

        except:
            logger.exception("Screenshot Error. Restarting...")
            continue
        
        # Check if the title is profane
        try:
            profane = is_profane(title)
            logger.info(f"Profane: {profane}")
        except:
            profane = False
            logger.exception("Profanity Error.")

        # Splice the screenshot into individual images
        try:
            splices = splice_images(image,mser = True if profane else False)
            logger.info(f"Splces: {len(splices)}")
        except:
            logger.exception("Splice Error. Restarting...")
            continue
        
        # Check if the splices contains skin
        try:
            skin = skin_pixels(splices) if len(splices) else False
            logger.info(f"Skin: {skin}")
        except:
            skin = False
            logger.exception("Skin Error.")
        
        # Check if the entire image is B&W
        try:
            bw = not color_in_image(image)
            logger.info(f"Black and White: {bw}")
        except:
            bw = False
            logger.exception("Black and White Error.")


        # If the image contains skin or the title is profane, and there are splices, then check for NSFW
        opennsfw = OpenNsfw()
        if (skin or bw or profane) and len(splices):
            
            # Remove spilces that dont contain skin if the image is not completely B&W
            if not bw:
                try:
                    filtered_splices = [s for s in splices if skin_pixels(s, threshold=0.1)]
                    logger.info(f"Skin Splices: {len(filtered_splices)}")
                except:
                    filtered_splices = splices
                    logger.exception("Filter Error.")
            else:
                filtered_splices = splices
                    
            
            # Check if the splices are NSFW
            try:
                filtered_splices = [s for s in filtered_splices if opennsfw.is_nsfw(s)]
                logger.info(f"NSFW Splices: {len(filtered_splices)}")
            except:
                logger.exception("NSFW Error. Restarting OpenNSFW...")
                opennsfw = OpenNsfw()

            logger.info(f"Filtered Splices: {len(filtered_splices)}")
            if not len(filtered_splices):
                continue
            
            # Add the screenshot to the queue
            queue.put(dict(image=image,title=title,exec_name=exec_name,splices=filtered_splices,))
            logger.info("Add to Queue: True")
            continue

        logger.info(f"Add to Queue: False")
        del opennsfw
        
        sleep_time = max_screen_per_second - (time.time() - start_time)
        if sleep_time > 0:
            time.sleep(sleep_time)


def detect_process(
    queue: multiprocessing.Queue,
):
    # Logger
    logger = logging.getLogger("detect")
  
    # Imports
    logger.info("Starting Detect Process...")
    import django
    django.setup() # This is required for multiprocessing
    from creep_app.models import Screenshot
    from creep_app.brain import NudeNet

    # Set the initial values
    raw_screenshots = []
    
    # Loop forever
    while True:
        
        # Get all the screenshota from the queue
        while not queue.empty():
            raw_screenshots.append(queue.get())

        logger.debug(f"Raw screenshots: {len(raw_screenshots)}")

        # If the queue is empty, then continue
        if len(raw_screenshots) == 0:
            logger.debug("Queue is empty. Sleeping...")
            time.sleep(5)
            continue
        else:
            logger.debug("Queue is not empty. Processing...")

        # Createe the NudeNet instance
        brain = NudeNet()

        # Loop through the screenshots
        for raw_screenshot in raw_screenshots:
            image = raw_screenshot["image"]
            title = raw_screenshot["title"]
            exec_name = raw_screenshot["exec_name"]
            splices = raw_screenshot["splices"]

            logger.debug(f"Title: {title}")
            logger.debug(f"Exec name: {exec_name}")
            logger.debug(f"Raw Splices: {len(splices)}")

            # Loop through the splices
            for splice in splices:

                # Check if the splice is NSFW
                try:
                    result = brain.detect([splice])[0]["is_nsfw"]
                    logger.debug(f"Result: {result}")
                except:
                    logger.exception("Detect Error. Restarting NudeNet...")
                    brain = NudeNet()
                    continue

                # If the splice is NSFW, then save the screenshot
                if result:
                    logger.info("Saving Screenshot")
                    Screenshot.save_screenshot(
                        image,title,exec_name,is_nsfw=result,keep=False,
                    )
                    break
                else:
                    time.sleep(1)
            else:
                # Even if the splice is not NSFW, save the screenshot 1/10 of the time
                if randint(1, 10) == 1:
                    logger.info("Saving Screenshot")
                    Screenshot.save_screenshot(
                        image,
                        title,
                        exec_name,
                        is_nsfw=result,
                        keep=True,
                    )
        logger.info("Finished Detection")

        # Clear variables
        raw_screenshots = []
        brain = None
        
        # Sleep for 60 seconds
        time.sleep(60)


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
    # p3 = multiprocessing.Process(
    #    target=alert_process,
    # )
    p1.daemon = True
    p2.daemon = True
    # p3.daemon = True
    p1.start()
    p2.start()
    # p3.start()
    p1.join()
    p2.join()
    # p3.join()
