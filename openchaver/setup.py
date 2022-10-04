import json
import oschmod
import stat
import shutil
from . import config_path , BASE_DIR

def setup_user(userid, uninstall_code):
    """Setup the user on the client computer"""
    
    # Check if config_path exists
    if config_path.exists() and config_path.is_file() and config_path.stat().st_size > 0:
        raise FileExistsError("Config file already exists")
    
    # Create config file
    config = {
        "userid": userid,
        "uninstall_code": uninstall_code
    }
    with open(config_path, "w") as f:
        json.dump(config, f)
    
    oschmod.set_mode(str(config_path),  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)

def uninstall(uninstall_code,remove_user=True,delete_files=True):
    """Uninstall the program from the client computer"""
    
    # Check if config_path exists
    if config_path.exists():
        try: # Assert the uninstall code is correct
            assert json.load(open(config_path))["uninstall_code"] == uninstall_code
        except AssertionError: # If the uninstall code is incorrect raise an error
            raise ValueError("Uninstall code is incorrect")
        except: # If the config file is empty or corrupt, delete it
            config_path.unlink(missing_ok=True)
    
    if remove_user or delete_files:
        config_path.unlink(missing_ok=True)
    
    if delete_files:
        shutil.rmtree(BASE_DIR, ignore_errors=True)

        