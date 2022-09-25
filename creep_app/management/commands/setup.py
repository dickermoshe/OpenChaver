from django.core.management.base import BaseCommand, CommandError

from creep_app.models import Config

class Command(BaseCommand):
    help = 'Run the Creep App'

    def handle(self, *args, **options):
        Config.add_account()
        Config.send_email('Hello',"Hello World")
        
