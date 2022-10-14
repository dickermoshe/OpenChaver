import datetime

import dataset
from dataset.database import Database
from dataset.table import Table
from sqlalchemy import UnicodeText, Boolean, JSON, DateTime

from .utils import chmod, obfuscate_text, obfuscate_image, encode_numpy_to_base64
from .const import SYSTEM_DATA_DIR , LOCAL_DATA_DIR
from .window import Window

class DB:
    def __init__(self):
        # Initialize the database
        self.db : Database = dataset.connect(f'sqlite:///{self.db_path}')

        # This is a hack to make sure the database is created
        table : Table = self.db.create_table('init')
        table.insert(dict(name='init', value='init'))

        # Set the permissions on the database
        chmod(self.db_path)
        self.table : Table = self.db[self.table_name]


class ScreenshotDB(DB):
    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()
        self.db_path = SYSTEM_DATA_DIR / f'{self.table_name}.db'
        super().__init__()
    
    def save_window(self,window:Window):
        ob_title = obfuscate_text(window.title)
        ob_exec_name = obfuscate_text(window.exec_name)
        ob_image = obfuscate_image(window.image)
        ob_base64_image = encode_numpy_to_base64(ob_image)

        data = dict(
            # Obfuscated data
            title=ob_title,
            exec_name=ob_exec_name,
            base64_image=ob_base64_image,

            # Window data
            profane=window.profane,
            nsfw=window.is_nsfw,
            nsfw_detections = window.nsfw_detections if window.nsfw_detections is not None else {},
            created=datetime.datetime.now(),
        )

        types = dict(
            title=UnicodeText,
            exec_name=UnicodeText,
            profane=Boolean,
            base64_image=UnicodeText,
            nsfw=Boolean,
            nsfw_detections = JSON,
            created=DateTime,
        )
        self.table.insert(data,ensure=True,types=types)

class ConfigurationDB(DB):
    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()
        self.db_path = LOCAL_DATA_DIR / f'{self.table_name}.db'
        super().__init__()

    def save_device_id(self,device_id) -> bool:
        data = dict(
            device_id=device_id,
        )
        types = dict(
            device_id=UnicodeText,
        )

        if self.table.find_one():
            return False

        self.table.insert(data,ensure=True,types=types)
        return True
    
    @property
    def is_configured(self) -> bool:
        return bool(self.table.find_one())
    
    @property
    def device_id(self) -> str|None:
        try:
            return self.table.find_one()["device_id"]
        except:
            return None
