import os
from ..logger import handle_error
import logging
import time

logger = logging.getLogger(__name__)
if os.name == 'nt':
    from ..const import MONITOR_COMMAND
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
                    if cmd[-1] == 'runmonitor' and cmd[-2].endswith(
                            ('openchaver.py', 'openchaver.exe')):
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

                win32process.CreateProcessAsUser(token, None, MONITOR_COMMAND,
                                                 None, None, False,
                                                 win32con.CREATE_NEW_CONSOLE,
                                                 None, None,
                                                 win32process.STARTUPINFO())
                logger.info(f"Started monitor for {username}")
            time.sleep(interval)
