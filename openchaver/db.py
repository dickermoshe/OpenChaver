import datetime
import logging
import dataset
from dataset.database import Database , Table
from sqlalchemy import UnicodeText, Boolean, JSON, DateTime
from pathlib import Path
import oschmod

from .utils import obfuscate_text, obfuscate_image, encode_numpy_to_base64
from .const import SCREENSHOT_DB, CONFIG_DB
from .window import Window

logger = logging.getLogger(__name__)

class DB:
    def __init__(self, db_file: Path,public = False):
        """
        Base class for the database

        Args:
            system (bool, optional): Use the system database. Defaults to False.
            user (bool|str, optional): Use the user database. Defaults to False. If a string is passed, it will be used as the database location.
        """
        self.table_name = self.__class__.__name__.lower()
        self.db_file = db_file

        # Create parent directories if they don't exist
        if not self.db_file.parent.exists():
            self.db_file.parent.mkdir(parents=True)

        exist = self.db_file.exists()

        # Initialize the database
        self.db : Database = dataset.connect(f'sqlite:///{self.db_file}')

        # Create the table if it doesn't exist
        if not exist:
            t : Table = self.db['init'] # This is a hack to make sure the database is created
            t.insert(dict(a=1))

            if public:
                oschmod.set_mode(str(self.db_file), 'a+rwx')

        # Set Table
        self.table : Table = self.db[self.table_name]

class ScreenshotDB(DB):
    def __init__(self) -> None:
        super().__init__(SCREENSHOT_DB,public=False)
    
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

def get_screenshot_db():
    return ScreenshotDB()

class ConfigurationDB(DB):
    def __init__(self) -> None:
        super().__init__(CONFIG_DB,public=True)
    
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
