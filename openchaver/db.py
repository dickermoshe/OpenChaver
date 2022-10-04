from pprint import pprint
import dataset
import time
import oschmod
import stat
from . import image_database_path, image_database_url,config_database_path, config_database_url
from .window import WinWindow as Window



class ImageDB:
    def __init__(self) -> None:
        self.create_db()

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
                self.create_db(recreate=True)
                self.save_window(window, recursive=True)
            else:
                raise

    def create_db(self, recreate=False):

        if recreate and image_database_path.exists():
            image_database_path.unlink()

        try:
            self.db = dataset.connect(image_database_url)
        except:
            # Delete the database file and try again
            image_database_path.unlink()
            self.db = dataset.connect(image_database_url)
        
        # Just to create the sqlite file
        self.db['init'].insert(dict(timestamp=time.time()))
        
        
        # Set the file permissions to block other users and groups from accesing the database
        oschmod.set_mode(str(image_database_path),  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        
        self.image_table = self.db["images"]

        

class ConfigDB:
    def __init__(self) -> None:
        new_db = not config_database_path.exists()
        self.db = dataset.connect(config_database_url)
        
        self.db['init'].insert(dict(timestamp=time.time()))
        
        if new_db:
            oschmod.set_mode(str(config_database_path),  stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
        
        self.user_table = self.db["user"]
    
    def save_user(self, userid, uninstall_code):
        self.user_table.insert(dict(userid=userid, uninstall_code=uninstall_code))
    
    def get_user(self):
        return self.user_table.find_one()
    
    @property
    def user_exist(self):
        return self.get_user() is not None
