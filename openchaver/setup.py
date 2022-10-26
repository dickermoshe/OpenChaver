import os
from pathlib import Path
import subprocess
import psutil
import logging
import shutil
from .utils import to_str
from .const import (SERVICE_NAME, BASE_EXE, SERVICE_ARGS, INSTALL_DIR,
                    TESTING, WATCHER_NAME, WATCHER_ARGS,SERVICE_LOGS, WATCHER_LOGS)

logger = logging.getLogger(__name__)


def create_service(name: str, exe: str | Path, args: str,log_file:Path):
    """
    This function creates a service using nssm.exe
    """
    if os.name == 'nt':
        logger.info(f"Creating the OpenChaver Service: {name}")

        nssm_path = Path(
            'C:\\nssm.exe'
        ) if TESTING else INSTALL_DIR / 'nssm.exe'  # noqa: E501

        if TESTING and not nssm_path.exists():
            shutil.copyfile((INSTALL_DIR / 'bin' / 'nssm.exe'), nssm_path)

        # Edit the service if it exists
        if name in [i.name() for i in psutil.win_service_iter()]:
            # Stop the service
            logger.info("Stopping the OpenChaver Service")
            subprocess.run(to_str([nssm_path, 'stop', name]))
            # Set the service executable
            logger.info("Updating the OpenChaver Service")
            subprocess.run(to_str([nssm_path, 'set', name, 'Application',
                                   exe]))
            # Set the service arguments
            subprocess.run(
                to_str([nssm_path, 'set', name, 'AppParameters', args]))
        else:
            # Create the OpenChaver Service
            logger.info(f"Creating {name}")
            subprocess.run(to_str([nssm_path, 'install', name, exe, args]))

        # Auto Start the OpenChaver Service
        logger.info(f"Auto Starting {name}")
        subprocess.run(
            to_str([nssm_path, 'set', name, 'Start', 'SERVICE_AUTO_START']))

        # Set the OpenChaver Service to run restart on failure
        subprocess.run(
            to_str([nssm_path, 'set', name, 'AppExit', 'Default', 'Restart']))

        # Set logging
        subprocess.run(
            to_str([
                nssm_path, 'set', name, 'AppStderr',
                log_file
            ]))
        
        # Set Log Rotation
        subprocess.run(
            to_str([
                nssm_path, 'set', name, 'AppRotateFiles', '1'
            ]))
        subprocess.run(
            to_str([
                nssm_path, 'set', name, 'AppRotateBytes', str(1024 * 1024 * 10)
            ]))
        subprocess.run(
            to_str([
                nssm_path, 'set', name, 'AppRotateOnline', '1'
            ]))
        subprocess.run(
            to_str([
                nssm_path, 'set', name, 'AppRotateFiles', '5'
            ]))

        # Start the OpenChaver Service
        logger.info(f"Starting {name}")
        subprocess.run(to_str([nssm_path, 'start', name])) 


        # Start the OpenChaver Service
        logger.info(f"Starting the OpenChaver Service")
        subprocess.run(to_str([nssm_path, 'start', name]))

        logger.info(f"OpenChaver Service Created: {name}")

        # Start the OpenChaver Service
        subprocess.run(to_str([nssm_path, 'start', name]))


def run_setup():
    """
    This script creates the following if they dont exist:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    Start the following if not started:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    """
    create_service(SERVICE_NAME, BASE_EXE, SERVICE_ARGS,SERVICE_LOGS)
    create_service(WATCHER_NAME, BASE_EXE, WATCHER_ARGS, WATCHER_LOGS)
