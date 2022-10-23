import os
if os.name ==   'nt' :
    from ..const import BASE_EXE,MONITOR_ARGS
    from ..utils import to_str
    import psutil
    import win32ts
    import win32process
    import win32con

    def monitor_is_running(username:str)->bool:
        """Check if the monitor is on"""
        command = to_str([BASE_EXE,MONITOR_ARGS])
        for proc in psutil.process_iter():
            try:
                if proc.username() == username:
                    if proc.cmdline() == command:
                        return True
            except:
                pass
        return False
        
    def keep_alive():
        """Return a list of logged in users"""

        
        command = ' '.join(to_str([BASE_EXE,MONITOR_ARGS]))

        for session in win32ts.WTSEnumerateSessions(win32ts.WTS_CURRENT_SERVER_HANDLE):
            id = session['SessionId']

            if id == 0:
                continue

            username = win32ts.WTSQuerySessionInformation(
                win32ts.WTS_CURRENT_SERVER_HANDLE,
                id,
                win32ts.WTSUserName
            )
            
            if monitor_is_running(username):
                continue

            # Get the token of the logged in user
            token = win32ts.WTSQueryUserToken(id)

            # Create a new process with the token of the logged in user
            win32process.CreateProcessAsUser(
                token,
                None,
                command,
                None,
                None,
                0,
                win32con.CREATE_NEW_CONSOLE,
                None,
                None,
                win32process.STARTUPINFO()

            )