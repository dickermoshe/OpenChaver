import datetime
import logging
import stat
import dataset
from dataset.database import Database
from dataset.table import Table
from sqlalchemy import UnicodeText, Boolean, JSON, DateTime

from .utils import obfuscate_text, obfuscate_image, encode_numpy_to_base64, chmod
from .const import SYSTEM_DATA_DIR, USER_DATA_DIR
from .window import Window

logger = logging.getLogger(__name__)

class DB:
    def __init__(self, system=False,user=False):
        self.table_name = self.__class__.__name__.lower()

        if system and not user:
            self.db_file = SYSTEM_DATA_DIR /  f"{self.table_name}.db"
        elif user and not system:
            self.db_file = USER_DATA_DIR /  f"{self.table_name}.db"
        else:
            raise ValueError("Must specify system or local database")

        # Initialize the database
        self.db : Database = dataset.connect(f'sqlite:///{self.db_file}')

        # This is a hack to make sure the database is created
        if not self.db_file.exists():
            table : Table = self.db.create_table('init',)
            table.insert(dict(name='init', value='init'), ensure=False)

        self.table : Table = self.db[self.table_name]
        
        # If the database is owned by the system,
        # Make sure that the database file can be read by everyone
        if system:
            mode = stat.S_IRUSR | stat.S_IWUSR | stat.S_IRGRP | stat.S_IWGRP | stat.S_IROTH | stat.S_IWOTH
            try:
                chmod(self.db_file, mode)
            except:
                logger.exception("Failed to set permissions on database file")
        else:
            logger.info("Database is not system owned, not setting permissions")



class ScreenshotDB(DB):
    def __init__(self) -> None:
        super().__init__(user=True,system=False)
    
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
        super().__init__(system=True,user=False)

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

def get_configuration_db():
    return ConfigurationDB()
