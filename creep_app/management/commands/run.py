from django.core.management.base import BaseCommand, CommandError

from creep_app.views import single_service

class Command(BaseCommand):
    help = 'Run the Creep App'

    def handle(self, *args, **options):
        single_service('Hello')
        
