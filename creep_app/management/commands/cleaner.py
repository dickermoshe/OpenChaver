from datetime import timedelta

from django.utils import timezone
from django.core.management.base import BaseCommand

from creep_app.models import Image

class Command(BaseCommand):
    help = 'This will delete old images'

    def handle(self, *args, **options):

        # Get all images older than 1 day that arent marked as keep
        images = Image.objects.filter(created__lt=timezone.now() - timedelta(days=1), keep=False, is_nsfw=False)

        # Delete the image files
        for image in images:
            image.image.delete()
        
        # Delete the database entries
        images.delete()


        # Get ALL images older than 7 days
        images = Image.objects.filter(created__lt=timezone.now() - timedelta(days=7))

        # Delete the image files
        for image in images:
            image.image.delete()

        # Delete the database entries
        images.delete()
            



        
        