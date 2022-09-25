import logging
import time
from mss.windows import MSS
import numpy as np
import cv2 as cv

from django.db import models
from django.utils.html import mark_safe
from django.core.files.base import ContentFile

from creep_app.window import Window

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

    #: Alerted
    alerted = models.BooleanField(default=False)

    #: Whether or not to keep the image for 7 days
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
    def grab_screenshot(
        cls,
        sct: MSS,
        max_tries: int,
        invalid_title: str | None = None,
        stable_window: bool | int = True,

    ):
        """
        Grabs a screenshot from the active window
        :param sct: The MSS client
        :param max_tries: The maximum amount of times to try to grab a screenshot before not waiting any longer
        :return: The screenshot as a cv2 image, the window title, and the window executable name
        """
        # If max_tries is at 0 then return whatever is in the active window
        if max_tries == 0:
            window = Window.activeWindow()
            if window is None:
                logger.warning("Window not found")
                return None, None, None
            else:
                logger.info("Found window: %s", window.title)
                return window.image(sct), window.title, window.exec_name
        
        # Otherwise, Respect the stable_window and invalid_title parameters
        else:
            window = Window.activeWindow(invalid_title=invalid_title)
            if window is None:
                time.sleep(0.5)
                return cls.grab_screenshot(sct, max_tries - 1, invalid_title, stable_window)
            
            if stable_window != False:
                for _ in range(int(stable_window) * 2):
                    if window.is_stable() == False:
                        time.sleep(0.5)
                        return cls.grab_screenshot(sct, max_tries - 1, invalid_title, stable_window)
                    time.sleep(0.5)
            
            logger.info("Found window: %s", window.title)
            return window.image(sct), window.title, window.exec_name
            
    @classmethod
    def save_screenshot(
        cls,
        img: np.ndarray,
        title: str,
        exec_name: str,
        keep: bool = False,
        is_nsfw: bool | None = None,
    ):
        """
        Save an image to the database

        :param img: The image to save
        :param title: The title of the window that the screenshot was taken from
        :param exec_name: The executable name of the window that the screenshot was taken from
        :return: The screenshot object or None if the image could not be saved
        """

        # Create a screenshot object
        try:
            screenshot = cls()
            _, buffer = cv.imencode(".png", img)
            screenshot.image.save(f"{int(time.time())}.png", ContentFile(buffer))
            screenshot.title = title
            screenshot.exec_name = exec_name
            screenshot.keep = keep
            screenshot.is_nsfw = is_nsfw
            screenshot.save()
            return screenshot
        except:
            logger.exception("Could not save screenshot")
            return None



class Alert(models.Model):
    """This is the model for an alert"""

    #: The screenshot that triggered the alert
    screenshots = models.ManyToManyField(Screenshot , related_name="alerts")

    # Whether or not the alert has been sent
    sent = models.BooleanField(default=False)

    #: The date and time the alert was created
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert {self.id}"

    class Meta:
        ordering = ["-created"]
    
    def send(self):
        """Send the alert"""
        print("Sending alert")
        self.sent = True
        self.save()
    
    @classmethod
    def send_alerts(cls):
        pass

# class Report(models.Model):
#     """A report of a nsfw content"""

#     #: The screenshots that were reported
#     screenshots = models.ManyToManyField(Screenshot , related_name="reports")

#     #: Report Sent
#     sent = models.BooleanField(default=False)

#     #: Timestamp of when the report was created
#     created = models.DateTimeField(auto_now_add=True)

#     @classmethod
#     def make_reports(cls):
#         """
#         Make reports of all the nsfw content

#         :return: None
#         """
#         screenshots = Screenshot.objects.filter(is_nsfw=False, keep=False)

#         # Break screenshots into groups of the hour they were taken
#         screenshot_groups = {}
#         for screenshot in screenshots:
#             hour = screenshot.created.strftime("%Y-%m-%d %H")
#             if hour not in screenshot_groups:
#                 screenshot_groups[hour] = []
#             screenshot_groups[hour].append(screenshot)

#         # Mark 1 random screenshot from each group as keep
#         for screenshots in screenshot_groups.values():
#             random_index = randint(0, len(screenshots) - 1)
#             screenshots[random_index].keep = True
#             screenshots[random_index].save()

#         # Delete all screenshots that are not marked as keep and are not nsfw
#         screenshots = Screenshot.objects.filter(is_nsfw=False, keep=False)
#         for screenshot in screenshots:
#             try:
#                 screenshot.image.delete()
#             except:
#                 pass
#             screenshot.delete()

#         # Create a report for each group
#         screenshots = Screenshot.objects.filter(is_nsfw=True)
#         screenshot_groups = {}
#         for screenshot in screenshots:
#             hour = screenshot.created.strftime("%Y-%m-%d %H")
#             if hour not in screenshot_groups:
#                 screenshot_groups[hour] = []
#             screenshot_groups[hour].append(screenshot)
#         for screenshots in screenshot_groups.values():
#             report = cls.objects.create()
#             report.screenshots.set(screenshots)
#             report.save()

#         # Delete all reports that are older than 7 days
#         for report in cls.objects.filter(
#             created__lte=datetime.now() - timedelta(days=7)
#         ):
#             report.delete()
