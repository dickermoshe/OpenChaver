# Custom command to run the monitor
# Path: monitor\management\commands\monitor.py
from pathlib import Path
import subprocess
import psutil
import logging
import shutil
import os

from django.core.management.base import BaseCommand

from openchaver.const import (
    INSTALL_DIR,
    MIGRATE_COMMAND,
    TESTING,
    BASE_EXE,
    SERVICE_NAME,
    WATCHER_NAME,
    SERVICE_LOGS,
    WATCHER_LOGS,
    MIGRATE_COMMAND,
    SERVICE_ARGS,
    WATCHER_ARGS,
)

logger = logging.getLogger(__name__)


def create_service(name: str, exe: str | Path, args: str, log_file: Path):
    """
    This function creates a service using nssm.exe
    name: The name of the service
    exe: The executable to run
    args: The arguments to pass to the executable
    log_file: The log file to write to
    """
    # Migrate the database
    logger.info("Migrating the database")
    subprocess.run(MIGRATE_COMMAND)

    if os.name == "nt":
        logger.info(f"Creating the OpenChaver Service: {name}")

        nssm_path = (
            Path("C:\\nssm.exe") if TESTING else INSTALL_DIR / "nssm.exe"
        )  # noqa: E501

        if TESTING and not nssm_path.exists():
            shutil.copyfile((INSTALL_DIR / "bin" / "nssm.exe"), nssm_path)

        # Edit the service if it exists
        if name in [i.name() for i in psutil.win_service_iter()]:
            # Stop the service
            logger.info("Stopping the OpenChaver Service")
            subprocess.run([str(nssm_path), "stop", name])

            # Set the service executable
            logger.info("Updating the OpenChaver Service")
            subprocess.run([str(nssm_path), "set", name, "Application", str(exe)])

            # Set the service arguments
            subprocess.run([str(nssm_path), "set", name, "AppParameters", str(args)])
        else:
            # Create the OpenChaver Service
            logger.info(f"Creating {name}")
            subprocess.run([str(nssm_path), "install", name, str(exe), str(args)])

        # Auto Start the OpenChaver Service
        logger.info(f"Auto Starting {name}")
        subprocess.run([str(nssm_path), "set", name, "Start", "SERVICE_AUTO_START"])

        # Set the OpenChaver Service to run restart on failure
        subprocess.run([str(nssm_path), "set", name, "AppExit", "Default", "Restart"])

        # Set logging
        subprocess.run([str(nssm_path), "set", name, "AppStderr", str(log_file)])

        # Set Log Rotation
        subprocess.run([str(nssm_path), "set", name, "AppRotateFiles", "1"])
        subprocess.run(
            [str(nssm_path), "set", name, "AppRotateBytes", str(1024 * 1024 * 10)]
        )

        subprocess.run([str(nssm_path), "set", name, "AppRotateOnline", "1"])
        subprocess.run([str(nssm_path), "set", name, "AppRotateFiles", "5"])

        # Start the OpenChaver Service
        logger.info(f"Starting {name}")
        subprocess.run([str(nssm_path), "start", name])

        # Start the OpenChaver Service
        logger.info(f"Starting the OpenChaver Service")
        subprocess.run([str(nssm_path), "start", name])

        logger.info(f"OpenChaver Service Created: {name}")

        # Start the OpenChaver Service
        subprocess.run([str(nssm_path), "start", name])


class Command(BaseCommand):
    help = "Run the monitor"

    def handle(self, *args, **options):

        """
        This script creates the following if they dont exist:
            1. The OpenChaver Service
            2. The OpenChaver Auto Start Link in the Communal Startup Foler
        Start the following if not started:
            1. The OpenChaver Service
            2. The OpenChaver Auto Start Link in the Communal Startup Foler
        """
        SERVICE_ARGS_STR = subprocess.list2cmdline(SERVICE_ARGS)
        WATCHER_ARGS_STR = subprocess.list2cmdline(WATCHER_ARGS)
        create_service(SERVICE_NAME, BASE_EXE, SERVICE_ARGS_STR, SERVICE_LOGS)
        create_service(WATCHER_NAME, BASE_EXE, WATCHER_ARGS_STR, WATCHER_LOGS)
