import logging
from django.db import models

from .profanity import is_profane
from .image_utils import get_bounding_boxes, open_image  # noqa E501
from .nudity import Detector, Classifier

logger = logging.getLogger(__name__)


class Screenshot(models.Model):
    title = models.TextField()
    excutable_name = models.TextField()
    image_file = models.ImageField(upload_to="screenshots",)

    TYPES = (
        ("META", "META"),  # Archive the meta data. No image
        (
            'IMAGE', 'IMAGE'
        ),  # Archive the image and meta data. Don't process the image for NSFW
        (
            'NSFW', 'NSFW'
        ),  # Process the image for NSFW. Archive the image and meta data if NSFW
        (
            'NSFW_IMAGE', 'NSFW_IMAGE'
        ),  # Process the image for NSFW. Archive the image and meta data NSFW always
        (
            'NSFW_META', 'NSFW_META'
        ),  # Process the image for NSFW. Archive the meta data if NSFW. Don't archive the image
    )

    screenshot_type = models.TextField(
        choices=TYPES,
        default="META",
    )
    is_nsfw = models.BooleanField(null=True, blank=True)
    is_profane = models.BooleanField(null=True, blank=True)
    nsfw_detection = models.JSONField(default=list,
                                      blank=True,
                                      null=True,
                                      help_text="NSFW detection results")
    timestamp = models.DateTimeField(auto_now_add=True, )

    def __str__(self):
        return self.title

    @property
    def image(self):
        """Get the image as a numpy array"""
        if self.image_file:
            return open_image(self.image_file.path)

    def run_nsfw_detection(self):
        """Run the NSFW detection on the image"""

        image = self.image

        if image is None:
            return False, []

        sub_images = []
        for x, y, w, h in get_bounding_boxes(image):
            sub_images.append(image[y:y + h, x:x + w])

        classifier = Classifier()
        for i in sub_images:
            if classifier.is_nsfw(i):
                detector = Detector()
                detector_results = detector.is_nsfw(i)
                if detector_results['is_nsfw']:
                    return True, detector_results
        return False, []

    def post_process(self) -> "Screenshot":
        """Post process the screenshot"""
        self.is_profane = is_profane(self.title)
        self.is_nsfw, self.nsfw_detection = self.run_nsfw_detection()

        logger.info(
            f"Screenshot {self.title} |  NSFW: {self.is_nsfw} | Profane: {self.is_profane}"
        )

        if not self.is_nsfw:
            if self.screenshot_type == "NSFW":
                logger.info(f"Deleting {self.title} because it is not NSFW")
                self.delete()
            elif self.screenshot_type == "NSFW_META":
                logger.info(
                    f"Deleting {self.image_file} because it is not NSFW")
                self.image_file.delete()

            latest_screenshot = Screenshot.objects.exclude(
                pk=self.pk).order_by('-timestamp').first()

            if latest_screenshot and latest_screenshot.title == self.title:
                self.image_file.delete()
                self.delete()
                return None

        self.save()
        return self
