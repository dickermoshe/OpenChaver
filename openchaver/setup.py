import os
import psutil
import time
from . import BASE_DIR
from .db import ConfigDB


def setup(userid, uninstall_code):
    """Setup the user on the client computer"""
    
    db = ConfigDB()
    if db.user_exist:
        raise Exception("User already exists")
    else:
        db.save_user(userid, uninstall_code)

def kill_monitor():
    """Kill the monitor process"""
    db = ConfigDB()
    pid = db.get_pid("monitor")
    if pid:
        p = psutil.Process(pid)
        p.terminate()
        db.pid_table.delete(id=pid)
    else:
        raise Exception("Monitor process not found")
    

def run_uninstall_script():
    script = f"""
    On Error Resume Next
    WScript.Sleep 1000
    Set fso = CreateObject("Scripting.FileSystemObject")
    fso.DeleteFolder "{BASE_DIR}", True
    """
    with open("uninstall.vbs", "w") as f:
        f.write(script)
    os.startfile("uninstall.vbs")

def uninstall(uninstall_code):
    """Uninstall the program from the client computer"""
    db = ConfigDB()
    user = db.get_user()
    if user:
        if user["uninstall_code"] == uninstall_code:
            kill_monitor()
            db.user_table.delete(id=user["id"])
            time.sleep(1)
            run_uninstall_script()
        else:
            raise Exception("Invalid uninstall code")
    else:
        raise Exception("User not found")

def update():
    """Update the program on the client computer"""
    #TODO: Implement this function once the backend is ready
    pass