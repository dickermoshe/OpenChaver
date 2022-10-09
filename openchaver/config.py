import os
import time
import sys
from . import BASE_DIR
from .db import ConfigDB


def kill_other():
    """Kill any running instances of the program that is currently running, besides the current one"""
    import psutil
    current_pid = os.getpid()
    current_exe = psutil.Process(current_pid).exe()

    for process in psutil.process_iter():
        try:
            if process.pid != current_pid and process.exe() == current_exe:
                process.kill()
        except:
            pass


def run_uninstall_script():
    script = f"""
    On Error Resume Next
    WScript.Sleep 3000
    Set fso = CreateObject("Scripting.FileSystemObject")
    fso.DeleteFolder "{BASE_DIR}", True
    """
    with open("uninstall.vbs", "w") as f:
        f.write(script)
    os.startfile("uninstall.vbs")
    os.kill(os.getpid(), 9)

def uninstall():
    """Uninstall the program from the client computer"""
    db = ConfigDB()
    kill_other()
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