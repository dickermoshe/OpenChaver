import shutil
from . import BASE_DIR
from .db import ConfigDB

def setup(userid, uninstall_code):
    """Setup the user on the client computer"""
    
    db = ConfigDB()
    if db.user_exist:
        raise Exception("User already exists")
    else:
        db.save_user(userid, uninstall_code)

def uninstall(uninstall_code):
    """Uninstall the program from the client computer"""
    db = ConfigDB()
    user = db.get_user()
    if user:
        if user["uninstall_code"] == uninstall_code:
            db.user_table.delete(id=user["id"])
            shutil.rmtree(BASE_DIR)
        else:
            raise Exception("Invalid uninstall code")
    else:
        raise Exception("User not found")

def update():
    """Update the program on the client computer"""
    #TODO: Implement this function once the backend is ready
    pass