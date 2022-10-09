import os
import time

from . import BASE_DIR
from .db import ConfigDB
from .monitor import kill_monitor

def configure(device_id, uninstall_code):
    """Configure the client computer"""
    
    db = ConfigDB()
    if db.configured:
        raise Exception("User already exists")
    else:
        device = {
            "device": device_id,
            "uninstall_code": uninstall_code,
        }
        db.save_device(device)

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
            db.wipe_device()
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