from pathlib import Path
import dataset
import time
import oschmod
import stat
from . import BASE_DIR
from .window import WinWindow as Window


class BaseDB:
    def __init__(self,name:str,path : Path,is_restricted=True):
        self.db_file = path / name
        self.url = 'sqlite:///' + str(self.db_file)
        self.is_restricted = is_restricted
        self.create()
        self.connect()
    
    def create(self,recreate=False):
        if recreate and self.db_file.exists():
            self.db_file.unlink()

        if not self.db_file.exists() or recreate:
            self.db = dataset.connect(self.url)
            self.db.create_table('init')
            self.db['init'].insert(dict(time=time.time()))
            self.db.commit()
        
        if self.is_restricted:
            oschmod.set_mode(str(self.db_file),  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    
    def connect(self):
        self.db = dataset.connect(self.url)
        
class ImageDB(BaseDB):
    def __init__(self):
        super().__init__("images.db",BASE_DIR)
        self.image_table = self.db["images"]
    
    def pop_windows(self):
        for i in self.image_table:
            i = dict(i)
            i['image'] = i['image'].tolist()
            yield i
    
    def delete_window(self, id):
        self.image_table.delete(id=id)

    def save_window(self, window: Window, recursive=False):
        w = dict(
            title=window.title,
            profane=window.profane,
            nsfw=window.nsfw,
            exec_name=window.exec_name,
            image=window.image,
            timestamp=time.time(),
        )

        try:
            self.image_table.insert(w)

        # Due to the fact that this database is for temporary storage,
        # # any errors will promt the database to be deleted and recreated.
        # But only once.
        except:
            if not recursive:
                self.create(recreate=True)
                self.save_window(window, recursive=True)
            else:
                raise

class ConfigDB(BaseDB):
    def __init__(self) -> None:
        super().__init__("config.db",BASE_DIR.parent)
        self.device_table = self.db["device_table"]
        self.pid_table = self.db["pid"]
    
    def save_device(self, device: dict):
        # Check if any device is already registered
        if self.device_table.find_one():
            raise Exception("Device already registered")
        else:
            self.device_table.insert(device)
    
    def get_device(self):
        return self.device_table.find_one()
    
    def wipe_device(self):
        self.device_table.delete()

    def save_pid(self, process:str,pid:int):
        self.pid_table.upsert(dict(process=process,pid=pid),["process"])
    
    def get_pid(self, process:str):
        return self.pid_table.find_one(process=process)['pid']
    
    @property
    def configured(self):
        return self.get_device() is not None
