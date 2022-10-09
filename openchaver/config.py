import os
import time

from . import BASE_DIR
from .db import ConfigDB
from .monitor import kill_monitor

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

def uninstall():
    """Uninstall the program from the client computer"""
    db = ConfigDB()
    kill_monitor()
    db.wipe_device()
    time.sleep(1)
    run_uninstall_script()


def update():

    """Update the program on the client computer"""
    #TODO: Implement this function once the backend is ready
    pass

def gui():
    """Run the GUI"""
    from .gui import configure_gui, uninstall_gui
    from .db import ConfigDB
    
    db = ConfigDB()
    if db.configured:
        uninstall_gui(db.get_device()['device_id'])
    else:
        configure_gui()