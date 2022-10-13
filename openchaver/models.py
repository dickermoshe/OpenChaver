import string
import datetime

from dataset import Table
import numpy as np
import cv2 as cv

from sqlalchemy import UnicodeText, Boolean, LargeBinary, JSON, DateTime

from .image_utils.obfuscate import obfuscate_image
from image_utils.encoder import encode_numpy_to_base64, decode_base64_to_numpy
from .window import Window
from .db import db

def obfuscate_text(text:str):
    # Replace all vowels with the next vowel in the alphabet using regex
    a = string.ascii_letters
    b = string.ascii_letters[-1] + string.ascii_letters[:-1]
    table = str.maketrans(a, b)
    return text.translate(table)

def deobfuscate_text(text:str):
    # Replace all vowels with the next vowel in the alphabet using regex
    a = string.ascii_letters
    b = string.ascii_letters[-1] + string.ascii_letters[:-1]
    table = str.maketrans(b, a)
    return text.translate(table)
    
class ModelBase:
    def __init__(self) -> None:
        self.table : Table = db.db[self.table_name]

class ScreenshotModel(ModelBase):
    def __init__(self) -> None:
        self.table_name = self.__class__.__name__.lower()
        super().__init__()

    
    def from_window(self,window:Window):
        """Save a screenshot from a window"""

        # Text is obfuscated temporarily
        # Due to filters blocking the request.
        title = obfuscate_text(window.title)
        exec_name = obfuscate_text(window.exec_name)

        # The image is pixelated permanently
        # but also obfuscated temporarily by reversing it.
        image = obfuscate_image(window.image)

        image_string = encode_numpy_to_base64(image)

        data = dict(
            # Obfuscated data
            title=title,
            exec_name=exec_name,
            image=image_string,

            # Window data
            profane=window.profane,
            nsfw=window.is_nsfw,
            nsfw_detections = window.nsfw_detections,
            created_at=datetime.datetime.now(),
        )
        types = dict(
            title=UnicodeText,
            exec_name=UnicodeText,
            profane=Boolean,
            png=UnicodeText,
            nsfw=Boolean,
            nsfw_detections = JSON,
            created_at=DateTime,
        )
        self.table.insert(data,ensure=True,types=types)


    def get_all(self):
        """Get all screenshots as generator"""
        for row in self.table.all():
            d = row
            d['image'] = decode_base64_to_numpy(d['image'])
            yield d


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


    
