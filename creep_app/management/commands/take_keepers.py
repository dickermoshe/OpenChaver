import time
import cv2 as cv
import logging

from django.core.management.base import BaseCommand
from django.core.files.base import ContentFile

from creep_app.models import Image
from creep.heart import Heart

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'This will take pictures every 5 hours'

    def handle(self, *args, **options):
        heart = Heart()
        
        while True:
            img = heart.snap(after_title_change=False, after_stable_title=5)
            if img is not None:
                _, buf = cv.imencode('.jpg', img)
                file = ContentFile(buf.tobytes(), name='image.jpg')
                Image.objects.create(image=file, keep=True)
            time.sleep(18000)
