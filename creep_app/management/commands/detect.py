import cv2 as cv
import numpy as np
import logging

from django.core.management.base import BaseCommand

from creep_app.models import Image
from creep.brain import Brain


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'This will detect NSFW images'

    def handle(self, *args, **options):
        brain = Brain()

        unparsed_images = Image.objects.filter(is_nsfw=None)

        non_updated_images = []

        for unparsed_image in unparsed_images:

            img = cv.imdecode(np.frombuffer(unparsed_image.image.read(), np.uint8), 1)
        
            spliced_images = brain.splice(img)

            for spliced_image in spliced_images:
                
                result = brain.detect(spliced_image,fast=True)
                if result['is_nsfw'] == True:
                    unparsed_image.is_nsfw = True
                    break
            else:
                unparsed_image.is_nsfw = False

            non_updated_images.append(unparsed_image)

        Image.objects.bulk_update(non_updated_images, ['is_nsfw'])