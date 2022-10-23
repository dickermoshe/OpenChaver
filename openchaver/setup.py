import os
from pathlib import Path
import subprocess
import psutil
import logging
import shutil
from .utils import to_str

logger = logging.getLogger(__name__)


def run_setup():
    """
    This script creates the following if they dont exist:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    Start the following if not started:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    """
    if os.name == 'nt':
        # Create the OpenChaver Service
        from .const import (SERVICE_NAME, BASE_EXE, SERVICES_ARGS, INSTALL_DIR,
                            TESTING, MONITOR_COMMAND)
        logger.info(f"Creating the OpenChaver Service: {SERVICE_NAME}")
        logger.info(f'Basename: {BASE_EXE}')
        nssm_path = Path(
            'C:\\nssm.exe') if TESTING else INSTALL_DIR / 'nssm.exe'
        if TESTING and not nssm_path.exists():
            shutil.copyfile((INSTALL_DIR / 'bin' / 'nssm.exe'), nssm_path)

        # Edit the service if it exists
        if SERVICE_NAME in [i.name() for i in psutil.win_service_iter()]:
            # Stop the service
            logger.info("Stopping the OpenChaver Service")
            subprocess.run(to_str([nssm_path, 'stop', SERVICE_NAME]))
            # Set the service executable
            logger.info("Updating the OpenChaver Service")
            subprocess.run(
                to_str(
                    [nssm_path, 'set', SERVICE_NAME, 'Application', BASE_EXE]))
            subprocess.run(
                to_str([
                    nssm_path, 'set', SERVICE_NAME, 'AppParameters',
                    SERVICES_ARGS
                ]))
        else:
            # Create the OpenChaver Service
            logger.info(f"Creating {SERVICE_NAME}")
            subprocess.run(
                to_str([
                    nssm_path, 'install', SERVICE_NAME, BASE_EXE, SERVICES_ARGS
                ]))

        # Auto Start the OpenChaver Service
        logger.info(f"Auto Starting {SERVICE_NAME}")
        subprocess.run(
            to_str([
                nssm_path, 'set', SERVICE_NAME, 'Start', 'SERVICE_AUTO_START'
            ]))

        # Set the OpenChaver Service to run restart on failure
        subprocess.run(
            to_str([
                nssm_path, 'set', SERVICE_NAME, 'AppExit', 'Default', 'Restart'
            ]))

        # Set logging
        subprocess.run(
            to_str([
                nssm_path, 'set', SERVICE_NAME, 'AppStderr',
                INSTALL_DIR / 'service.log'
            ]))

        # Start the OpenChaver Service
        logger.info(f"Starting {SERVICE_NAME}")
        subprocess.run(to_str([nssm_path, 'start', SERVICE_NAME]))

        # Add registry key to start the monitor on startup
        # HKEY_LOCAL_MACHINE\Software\Microsoft\Windows\CurrentVersion\Run
        logger.info(f"Adding {SERVICE_NAME} to startup")
        subprocess.run(
            to_str([
                'reg', 'add',
                'HKLM\\Software\\Microsoft\\Windows\\CurrentVersion\\Run',
                '/v', SERVICE_NAME, '/t', 'REG_SZ', '/d', MONITOR_COMMAND, '/f'
            ]))
