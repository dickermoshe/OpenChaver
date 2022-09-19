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

        for unparsed_image in unparsed_images:

            img = cv.imdecode(np.frombuffer(unparsed_image.image.read(), np.uint8), 1)
            
            if brain.detect(img)['is_nsfw']:
                unparsed_image.is_nsfw = True
            else:
                spliced_images = brain.splice(img)
                for spliced_image in spliced_images:
                    if brain.detect(spliced_image,fast=True)['is_nsfw']:
                        unparsed_image.is_nsfw = True
                        break
                else:
                    unparsed_image.is_nsfw = False
            logger.info(f'Image {unparsed_image.id} is NSFW: {unparsed_image.is_nsfw}')

            unparsed_image.save()