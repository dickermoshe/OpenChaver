import logging
from django.core.management.base import BaseCommand
from core.watchdog import keep_service_alive

logger = logging.getLogger(__name__)



class Command(BaseCommand):
    help = "Keep the service alive"

    def handle(self, *args, **options):
        
        keep_service_alive()


        