import logging
from django.core.management.base import BaseCommand
from django.core.management import call_command
from core.watchdog import keep_monitor_alive, keep_watcher_alive
from openchaver.utils import thread_runner
from openchaver.const import PORT

logger = logging.getLogger(__name__)



class Command(BaseCommand):
    help = "Run the main service"

    def handle(self, *args, **options):
        # Start the server on a separate thread
        services = {
            # Server
            "Server": {
                "target": call_command,
                "args": ('runserver',str(PORT),'--noreload'),
                "kwargs": {},
                "daemon": True,
            },
            # Keep keep_monitor_alive alive
            "keep_monitor_alive": {
                "target": keep_monitor_alive,
                "args": (),
                "kwargs": {},
                "daemon": True,
            },
            # Keep keep_watcher_alive alive
            "keep_watcher_alive": {
                "target": keep_watcher_alive,
                "args": (),
                "kwargs": {},
                "daemon": True,
            },

        }
        thread_runner(services)


        