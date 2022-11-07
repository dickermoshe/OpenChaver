# Custom command to run the monitor
# Path: monitor\management\commands\monitor.py

from django.core.management.base import BaseCommand
from monitor.monitor_windows import run_monitor
from monitor.cleaner import run_cleaner
from openchaver.utils import thread_runner

class Command(BaseCommand):
    help = "Run the monitor"

    def handle(self, *args, **options):
        services = {
            # Monitor
            "Monitor": {
                "target": run_monitor,
                "args": (),
                "kwargs": {},
                "daemon": True,
            },
            # Cleaner
            "Cleaner": {
                "target": run_cleaner,
                "args": (),
                "kwargs": {},
                "daemon": True,
            },
        }
        thread_runner(services)