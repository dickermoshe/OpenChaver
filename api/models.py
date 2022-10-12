from typing import Type
from django.db import models
from .window import Window

from django.db import models
from solo.models import SingletonModel


class Configuration(SingletonModel):
    user_id = models.UUIDField(null=True, blank=True)
    device_id = models.UUIDField(null=True, blank=True)

    def __str__(self):
        return self.__class__.__name__
    
    @property
    def is_configurated(self) -> bool:
        return self.user_id is not None and self.device_id is not None


class Screenshot(models.Model):
    """
    Screenshot model
    """
    title = models.TextField()
    exec_name = models.TextField(max_length=100)
    png = models.BinaryField()
    
    profane = models.BooleanField(default=False)
    nsfw = models.BooleanField(default=False)
    nsfw_detections = models.JSONField(default=dict,blank=True,null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
    
    @classmethod
    def from_window(cls:Type["Screenshot"],window:Window):
        return cls(
            title=window.title,
            profane=window.profane,
            png=window.as_bytes,
            image=window.image,
            nsfw=window.is_nsfw,
            nsfw_detections = window.nsfw_detections,
        )


