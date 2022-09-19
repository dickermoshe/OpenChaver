# Custom comman
import time
import cv2 as cv
import numpy as np
import logging
from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from creep_app.models import Image

from creep.brain import Brain
from creep.heart import Heart


logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'This will take pictures whenever the Title of the Active Window changes and stays for 5 seconds'

    def handle(self, *args, **options):
        brain = Brain()

        unparsed_images = Image.objects.filter(is_nsfw=None)

        unsaved_images = []
        non_updated_images = []

        for unparsed_image in unparsed_images:

            img = cv.imdecode(np.frombuffer(unparsed_image.image.read(), np.uint8), 1)
        
            spliced_images = brain.splice(img)

            for spliced_image in spliced_images:
                
                result = brain.detect(spliced_image,fast=True)
                _, buf = cv.imencode('.jpg', spliced_image)
                file = ContentFile(buf.tobytes(), name='image.jpg')

                unsaved_images.append(Image(image=file, is_nsfw=result['is_nsfw'],parent_image=unparsed_image))

                if result['is_nsfw'] == True:
                    unparsed_image.is_nsfw = True
                    non_updated_images.append(unparsed_image)
                else:
                    unparsed_image.is_nsfw = False
                    non_updated_images.append(unparsed_image)

        Image.objects.bulk_update(non_updated_images, ['is_nsfw'])
        Image.objects.bulk_create(unsaved_images)

        
        
