import datetime
from dataset import Table

from sqlalchemy import UnicodeText, Boolean, LargeBinary, JSON, DateTime

from .window import Window
from .db import db



class ModelBase:
    def __init__(self) -> None:
        self.table : Table = db.db[self.table_name]

class ScreenshotModel(ModelBase):
    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()
        super().__init__()

    
    def from_window(self,window:Window):
        # Obfuscate the window title for the backend to clean up
        
        data = dict(
            title=window.title,
            exec_name=window.exec_name,
            profane=window.profane,
            png=window.as_bytes,
            nsfw=window.is_nsfw,
            nsfw_detections = window.nsfw_detections,
            created_at=datetime.datetime.now(),
        )
        types = dict(
            title=UnicodeText,
            exec_name=UnicodeText,
            profane=Boolean,
            png=LargeBinary,
            nsfw=Boolean,
            nsfw_detections = JSON,
            created_at=DateTime,
        )
        self.table.insert(data,ensure=True,types=types)

class ConfigurationModel(ModelBase):
    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()
        super().__init__()

    def set(self,user_id,device_id):
        data = dict(
            user_id=user_id,
            device_id=device_id,
        )
        types = dict(
            user_id=UnicodeText,
            device_id=UnicodeText,
        )

        if self.table.find_one():
            return False

        self.table.insert(data,ensure=True,types=types)
        return True
    
    @property
    def is_configured(self):
        return bool(self.table.find_one())



    
