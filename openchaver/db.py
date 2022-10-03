import dataset
import time
from sqlalchemy.exc import SQLAlchemyError
try:
    from . import image_database_path , image_database_url
    from .window import WinWindow as Window
except:
    from __init__ import image_database_path , image_database_url
    from window import WinWindow as Window

class DB:
    def __init__(self) -> None:
        try:
            self.db = dataset.connect(image_database_url)
        except:
            # Delete the database file and try again
            image_database_path.unlink()
            self.db = dataset.connect(image_database_url)
        self.image_table = self.db["images"]
    
    def save_window(self, window:Window,recursive=False):
        w = dict(
                title=window.title,
                profane=window.profane,
                nsfw = window.nsfw,
                exec_name=window.exec_name,
                image=window.image,
                timestamp = time.time()
            )
        try:
            self.image_table.insert(w)
        
        # Due to the fact that this database is for temporary storage,
        # # any errors will promt the database to be deleted and recreated.
        # But only once.
        except:
            if not recursive:
                image_database_path.unlink()
                self.db = dataset.connect(image_database_url)
                self.image_table = self.db["images"]
                self.save_window(window,recursive=True)
            else:
                raise
            


    

