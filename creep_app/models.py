import logging
from random import randint
import time
from datetime import timedelta
from datetime import datetime
from pathlib import Path

import mss
from mss.windows import MSS
import psutil
import numpy as np
import cv2 as cv

from django.db import models
from django.utils.html import mark_safe
from django.core.files.base import ContentFile

from creep_app.window import Window
from creep_app.brain import Brain

logger = logging.getLogger("django")


class Screenshot(models.Model):
    """This is the model for a screenshot"""

    #: The image file
    image = models.ImageField(upload_to="images/")

    #: Whether or not the image is NSFW
    is_nsfw = models.BooleanField(default=None, null=True, blank=True)

    #: The title of the window that the screenshot was taken from
    title = models.CharField(
        max_length=200,
    )

    #: The executable name of the window that the screenshot was taken from
    exec_name = models.CharField(
        max_length=200,
    )

    #: Whether or not to keep the screenshot after a negative result
    keep = models.BooleanField(default=False)

    #: The date and time the screenshot was created
    created = models.DateTimeField(auto_now_add=True)

    #: The date and time the screenshot was last updated
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image.name

    def image_tag(self):
        """Returns an image tag for the image for the admin page"""
        return mark_safe('<img src="/media/%s" width="300" />' % (self.image))

    class Meta:
        ordering = ["-created"]

    def cv_image(self):
        """
        Returns the image as a cv2 image.
        If the image file does not exist, the record is deleted. Returns None if the image file does not exist.
        :return: The image as a cv2 image or None if the image file does not exist
        """

        try:
            return cv.imread(self.image.path)
        except:
            self.delete()
            return None

    @classmethod
    def snap(
        cls,
        sct: MSS,
        after_title_change: bool = False,
        after_stable_title: int | bool = False,
        max_wait: int = 60,
        keep = False,
        final_window=None,
    ) -> None | np.ndarray:
        """
        Take a screenshot of a window and return the image as a cv2 image

        :param sct: The mss instance to use
        :param after_title_change: Whether or not to wait for the window title to change
        :param after_stable_title: Whether or not to wait for the window title to be stable for a certain amount of time
        :param max_wait: The maximum amount of time to wait for the correct conditions to be met before giving up
        :param initial_window: The window to use for the screenshot. If None, the active window will be used
        :param keep: Whether or not to keep the screenshot after a negative result
        :return: The screenshot as a cv2 image or None if the screenshot failed
        """

        # If the max_wait is at 0, return None
        if max_wait <= 0:
            logger.error("Timed out.")
            return None

        # If the final_window is not set, get the active window
        if final_window is None:
            # Get the initial window if it is not provided
            logger.info("Getting initial window...")
            initial_window, max_wait = Window.waitForActiveWindow(max_wait)

            # Check whether or not a window was found
            if initial_window is None:
                logger.warning("No initial_window found after %s seconds", max_wait)
                return None
            else:
                logger.info("Initial window found: %s", initial_window.title)

            # If after_title_change is True, wait for the title to change
            if after_title_change != False:
                logger.info("Waiting for title to change...")
                final_window, max_wait = Window.waitForActiveWindow(
                    max_wait, invalid_title=initial_window.title
                )

                # Check whether or not a window was found
                if final_window is None:
                    logger.warning("No final_window found afer %s seconds", max_wait)
                    return None
                else:
                    logger.info("Final window found: %s", final_window.title)
            # If after_title_change is False, use the initial window
            else:
                final_window = initial_window

        # If after_stable_title is True, wait for the title to be stable for 5 seconds
        if after_stable_title != False:
            logger.info("Waiting %s seconds for stable title...", after_stable_title)
            for _ in range(int(after_stable_title * 2)):
                stable_window, _ = Window.waitForActiveWindow(2)
                if stable_window == None or stable_window.title != final_window.title:
                    logger.info("Stable window title does not match final window title")
                    logger.info("Restarting snap with new max_wait: %s", max_wait)
                    return cls.snap(
                        sct,
                        after_title_change=after_title_change,
                        after_stable_title=after_stable_title,
                        max_wait=max_wait,
                        final_window=stable_window,
                    )
                else:
                    time.sleep(0.5)

            logger.info("Window is stable")

        # Get coordinates of the window
        window_coordinates = final_window.get_coordinates()
        logger.info("Window coordinates: %s", window_coordinates)

        # Take a screenshot of the window
        try:
            logger.info("Taking screenshot...")
            img = sct.grab(window_coordinates)
        except:
            logger.exception("Unable to grab screenshot")
            return None

        # Convert the screenshot to a cv2 image
        img = np.array(img)

        # Remove the alpha channel
        img = img[:, :, :3]

        cls.save_image(img, final_window.title, final_window.exec_name, keep)

    @classmethod
    def save_image(cls, img: np.ndarray, title: str, exec_name: str, keep=False):
        """
        Save an image to the database

        :param img: The image to save
        :param title: The title of the window that the screenshot was taken from
        :param exec_name: The executable name of the window that the screenshot was taken from
        :param keep: Whether or not to keep the screenshot after a negative result
        :return: The screenshot object or None if the image could not be saved
        """

        # Create a screenshot object
        screenshot = cls()

        # Only save the image if it contains skin pixels
        # However due to a simple Black and White Filter bypass we only do this 9/10 times
        if randint(0, 9) != 0 and keep == False:
            logger.info("Checking if image contains skin pixels...")
            img_copy = img.copy()
            blured = cv.GaussianBlur(img_copy, (5, 5), 0)

            min_HSV = np.array([0, 58, 30], dtype="uint8")
            max_HSV = np.array([33, 255, 255], dtype="uint8")

            imageHSV = cv.cvtColor(blured, cv.COLOR_BGR2HSV)
            skinRegionHSV = cv.inRange(imageHSV, min_HSV, max_HSV)

            if np.count_nonzero(skinRegionHSV) == 0:
                logger.info("Image does not contain skin pixels. Not saving.")
                return None
            else:
                logger.info("Image contains skin pixels. Saving.")

        # If the latest screenshot is very similar to the new screenshot, don't save it
        try:
            logger.info("Checking if image is similar to latest image...")
            latest_image = cls.objects.all().order_by("-created").first().cv_image()
            difference = cv.subtract(img, latest_image)
            b, g, r = cv.split(difference)
            if cv.countNonZero(b) + cv.countNonZero(g) + cv.countNonZero(r) < 100:
                logger.info("Image is similar to latest image. Not saving.")
                return None
        except:
            pass

        # Save the image to the database
        logger.info("Saving image")
        _, buffer = cv.imencode(".png", img)
        screenshot.image.save(f"{int(time.time())}.png", ContentFile(buffer))
        screenshot.keep = keep
        screenshot.title = title
        screenshot.exec_name = exec_name
        screenshot.save()

        return screenshot

    @classmethod
    def snap_service(
        cls,
        sleep_interval: int | list[int] = 0,
        after_title_change: bool = False,
        after_stable_title: int | bool = False,
        max_wait: int = 10,
        keep: bool = False,
    ):
        """
        Contantinously take screenshots of the active window

        :param sleep_interval: The amount of time to sleep between each screenshot
            an int will sleep for the same amount of time each time
            a list will sleep for a random amount of time between each screenshot
        :param after_stable_title: The amount of time to wait for the title to be stable
        :param after_title_change: The amount of time to wait for the title to change
        :param max_wait: The maximum amount of time to wait for a window to be active
        :param keep: Whether or not to keep the screenshot after a negative result

        :return: None
        """

        sct = mss.mss()
        while True:
            try:
                cls.snap(sct, after_title_change, after_stable_title , max_wait, keep=keep)
            except:
                logger.exception("Unable to snap screenshot. Reinitalizing mss")
                sct = mss.mss()
                continue
            time.sleep(sleep_interval if type(sleep_interval) == int else randint(sleep_interval[0], sleep_interval[1]))

    @classmethod
    def run_detections(cls, batch_size=10):
        """
        Run NSFW Detection on all images

        :param batch_size: The number of images to run detection on at once
        :return: None
        """
        brain = Brain()
        screenshots = cls.objects.filter(is_nsfw=None)

        # Run detection if one following conditions are met
        # 1. There are more than 10 images to be processed
        # 2. CPU usage is below 50%

        if len(screenshots) < 10 and psutil.cpu_percent() > 50:
            return

        # Remove screenshots whose images have been deleted
        for screenshot in screenshots:
            if not Path(screenshot.image.path).exists():
                logger.warning("Image file does not exist on disk %s", screenshot.title)
                screenshot.delete()
                continue

        # Group images into groups by image size
        screenshots = cls.objects.filter(is_nsfw=None)
        screenshot_groups = {}
        for screenshot in screenshots:
            image_width = screenshot.image.width
            image_height = screenshot.image.height
            image_size = f"{image_width}x{image_height}"
            if image_size not in screenshot_groups:
                screenshot_groups[image_size] = []
            screenshot_groups[image_size].append(screenshot)

        # Group each group into batches
        batches = []
        for images in screenshot_groups.values():
            # Add in batches of batch_size
            for i in range(0, len(images), batch_size):
                batches.append(images[i : i + batch_size])

        # Run detection on each batch
        for batch in screenshot_groups.values():

            # Open all the images
            images = [screenshot.cv_image() for screenshot in batch]

            # Check if any of the images did not load
            if len([i for i in images if i is None]):
                logger.warning("Unable to open one of the images. Skipping batch.")
                continue
            
            # Run detection
            results = brain.detect(images)
            print(results)
            # Save the results
            for screenshot, result in zip(batch, results):
                screenshot.is_nsfw = result["is_nsfw"]
                screenshot.save()

        # Delete all images that are not marked as keep and is_nsfw is 
        for screenshot in cls.objects.filter(keep=False, is_nsfw=False):
            Path(screenshot.image.path).unlink()
            screenshot.delete()

    @classmethod
    def clean(cls):
        """Delete all images older than 7 days"""
        for screenshot in cls.objects.filter(
            created__lte=datetime.now() - timedelta(days=7)
        ):
            screenshot.image.delete()
            screenshot.delete()
