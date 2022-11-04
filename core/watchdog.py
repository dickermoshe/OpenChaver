import os
from openchaver.decorators import handle_error, restart_on_exception
import logging
import time
import subprocess
from openchaver.const import MONITOR_COMMAND, WATCHER_NAME, SERVICE_NAME

def start_service_if_stopped(service_name: str):
    """Keep the service alive"""
    import os
    if os.name == 'nt':
        # Check if the service is running
        import win32serviceutil
        import win32service
        if win32serviceutil.QueryServiceStatus(
                service_name)[1] != win32service.SERVICE_RUNNING:  # noqa E501
            win32serviceutil.StartService(service_name)

logger = logging.getLogger(__name__)
if os.name == 'nt':
    
    import psutil
    import win32ts
    import win32process
    import win32con

    def monitor_is_running(username: str) -> bool:
        """Check if the monitor is on"""
        for proc in psutil.process_iter():
            try:
                u = proc.username().split('\\')[-1]
                if u == username:
                    cmd = proc.cmdline()
                    if cmd[1:]  == MONITOR_COMMAND[1:]:
                        return True
            except:  # noqa: E722
                pass
        logger.info("Monitor is not running for user %s", username)
        return False

    @handle_error
    def keep_monitor_alive(interval: int = 5):
        """Return a list of logged in users"""
        while True:
            for session in win32ts.WTSEnumerateSessions(
                    win32ts.WTS_CURRENT_SERVER_HANDLE):
                id = session['SessionId']

                if id == 0:
                    continue

                username = win32ts.WTSQuerySessionInformation(
                    win32ts.WTS_CURRENT_SERVER_HANDLE, id, win32ts.WTSUserName)

                if monitor_is_running(username):
                    continue

                # Get the token of the logged in user
                token = win32ts.WTSQueryUserToken(id)
                command = subprocess.list2cmdline(MONITOR_COMMAND)
                win32process.CreateProcessAsUser(token, None, command,
                                                 None, None, False,
                                                 win32con.CREATE_NO_WINDOW,
                                                 None, None,
                                                 win32process.STARTUPINFO())
                logger.info(f"Started monitor for {username}")
            time.sleep(interval)

    @restart_on_exception
    @handle_error
    def keep_watcher_alive():
        """This function Keeps the OpenChaver Watcher running"""

        logger.info("Starting the OpenChaver Watcher")
        while True:
            start_service_if_stopped(WATCHER_NAME)
            time.sleep(10)
            
    @restart_on_exception
    @handle_error
    def keep_service_alive():
        """This function Keeps the OpenChaver Service running"""

        logger.info("Starting the OpenChaver Service")
        while True:
            start_service_if_stopped(SERVICE_NAME)
            time.sleep(10)
    