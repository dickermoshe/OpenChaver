import datetime
import logging
import dataset
from dataset.database import Database
from sqlalchemy import UnicodeText, Boolean, JSON, DateTime
from pathlib import Path

from .utils import obfuscate_text, obfuscate_image, encode_numpy_to_base64
from .const import SYSTEM_DATA_DIR, USER_DATA_DIR
from .window import Window

logger = logging.getLogger(__name__)

class DB:
    def __init__(self, system=False,user:bool|str=False):
        """
        Base class for the database

        Args:
            system (bool, optional): Use the system database. Defaults to False.
            user (bool|str, optional): Use the user database. Defaults to False. If a string is passed, it will be used as the database location.
        """
        self.table_name = self.__class__.__name__.lower()

        if system and not user:
            self.db_path = SYSTEM_DATA_DIR / 'db' / f'{self.table_name}.db'
        elif user and not system and isinstance(user, bool):
            self.db_path = USER_DATA_DIR / 'db' / f'{self.table_name}.db'
        elif user and not system and isinstance(user, str) and Path(user).exists():
            self.db_path = Path(user)
        else:
            raise ValueError("Must specify system or local database")

        # Create parent directories if they don't exist
        if not self.db_path.parent.exists():
            self.db_path.parent.mkdir(parents=True)
    
        # Initialize the database
        self.db : Database = dataset.connect(f'sqlite:///{self.db_file}')

        # This is a hack to make sure the database is created
        Table = self.db.create_table('init',)

        self.table : Table = self.db[self.table_name]

class ScreenshotDB(DB):
    def __init__(self,path:str|None=None) -> None:
        if path == None:
            super().__init__(user=True,system=False)
        else:
            super().__init__(user=path,system=False)
    
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

def get_screenshot_db(path:str|None=None):
    return ScreenshotDB(path=path)

class ConfigurationDB(DB):
    def __init__(self) -> None:
        super().__init__(system=True,user=False,create=False)
    
    @property
    def is_configured(self) -> bool:
        return bool(self.table.find_one())
    
    @property
    def device_id(self) -> str|None:
        try:
            return self.table.find_one()["device_id"]
        except:
            return None

def get_configuration_db():
    return ConfigurationDB()
