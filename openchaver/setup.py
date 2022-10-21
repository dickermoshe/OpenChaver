import os
import subprocess
from pathlib import Path
import psutil
import logging
logger = logging.getLogger(__name__)

build_cmd = lambda cmd: [str(i) for i in cmd]

def run_setup():
    """
    This script creates the following if they dont exist:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    
    Start the following if not started:
        1. The OpenChaver Service
        2. The OpenChaver Auto Start Link in the Communal Startup Foler
    """

    # Create the OpenChaver Service
    from .const import SERVICE_NAME,NSSM_EXE, STARTUP_FOLDER,BASE_EXE, MONITOR_ARGS,SERVICE_ARGS

    # Remove the service if it exists
    if SERVICE_NAME in [i.name() for i in psutil.win_service_iter()]:
        logger.info(f"Removing {SERVICE_NAME}")
        subprocess.run(build_cmd([NSSM_EXE,'remove',SERVICE_NAME,'confirm']))

    # Create the OpenChaver Service
    cmd = build_cmd([NSSM_EXE,'install',SERVICE_NAME,BASE_EXE] + SERVICE_ARGS)
    logger.info("Creating OpenChaver Service")
    logger.info(f"Running: {cmd}")
    subprocess.run(cmd)

    # Start the OpenChaver Service
    cmd = build_cmd([NSSM_EXE,'start',SERVICE_NAME])
    logger.info("Starting OpenChaver Service")
    logger.info(f"Running: {cmd}")
    subprocess.run(cmd,)

    # Create the OpenChaver Auto Start Shortcut in the Communal Startup Foler
    from .utils import create_shortcut
    logger.info("Creating OpenChaver Auto Start Shortcut")
    SHORTCUT_PATH = STARTUP_FOLDER / f'{SERVICE_NAME}.lnk'
    create_shortcut(
        path = SHORTCUT_PATH,
        target = BASE_EXE,
        working_dir = Path.cwd(),
        args = subprocess.list2cmdline(MONITOR_ARGS),
        description = f"OpenChaver Auto Start Shortcut",)


    

    

    