import logging

from django.db import models
import django.dispatch

from .profanity import is_profane
from .image_utils import decode_base64_to_numpy, get_bounding_boxes # noqa E501
from .nudity import Detector, Classifier

logger = logging.getLogger(__name__)

class Screenshot(models.Model):
    title = models.TextField()
    excutable_name = models.TextField()
    base64_image = models.TextField(null=True, blank=True)

    TYPES = (
        ("META", "META"), # Archive the meta data. No image
        ('IMAGE', 'IMAGE'), # Archive the image and meta data. Don't process the image for NSFW
        ('NSFW', 'NSFW'), # Process the image for NSFW. Archive the image and meta data if NSFW
        ('NSFW_IMAGE', 'NSFW_IMAGE'), # Process the image for NSFW. Archive the image and meta data NSFW always
        ('NSFW_META', 'NSFW_META'), # Process the image for NSFW. Archive the meta data if NSFW. Don't archive the image
    )

    screenshot_type = models.TextField(choices=TYPES, default="META",)
    is_nsfw = models.BooleanField(null=True, blank=True)
    is_profane = models.BooleanField(null=True, blank=True)
    nsfw_detection = models.JSONField(default=list, blank=True, null=True, help_text="NSFW detection results")
    
    timestamp = models.DateTimeField(auto_now_add=True,)

    def __str__(self):
        return self.title
    
    @property
    def image(self):
        """Return the base64 string as a OpenCV image"""
        if self.base64_image:
            return decode_base64_to_numpy(self.base64_image)

    def run_nsfw_detection(self):
        if self.base64_image is None or self.is_nsfw is not None:
            self.is_nsfw = False
            self.save()
            return

        image = self.image
        sub_images = []
        
        for x, y, w, h in self.create_bounding_boxes():
            sub_images.append(image[y:y + h, x:x + w])
        
        classifier =  Classifier()
        for i in sub_images:
            if classifier.is_nsfw(i):
                # Run Detector on the images
                detector = Detector()
                detector_results = detector.is_nsfw(i)
                if detector_results['is_nsfw']:
                    self.is_nsfw = True
                    self.nsfw_detection = detector_results
                    break
        else:
            self.is_nsfw = False
        
        self.save()
        logger.info(f"NSFW detection complete for {self.title} - {self.is_nsfw}")

        if not self.is_nsfw:
            if self.screenshot_type == "NSFW":
                self.delete()
            elif self.screenshot_type == "NSFW_META":
                self.base64_image = None
                self.save()

    def run_profanity_detection(self):  
        if self.is_profane is None:
            self.is_profane = is_profane(self.title)
            self.save()

    def create_bounding_boxes(self) -> list:
        """Create bounding boxes for the images in the screenshot"""
        if self.base64_image is None:
            return []
        return get_bounding_boxes(self.image)


@django.dispatch.receiver(models.signals.post_save, sender=Screenshot)
def post_process(sender, instance: Screenshot, **kwargs):
    instance.run_profanity_detection()
    if instance.is_nsfw is None:
        instance.run_nsfw_detection()
    
    # Check if the instanve has been deleted
    if Screenshot.objects.filter(pk=instance.pk).exists():
        return
    
    # If the image is not NSFW and the latest screenshot has the same title
    # then delete the this one
    if not instance.is_nsfw:
        latest_screenshot = Screenshot.objects.exclude(pk=instance.pk).order_by('-timestamp').first()
        if latest_screenshot and latest_screenshot.title == instance.title:
            instance.delete()
            return


