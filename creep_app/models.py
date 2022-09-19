import logging
from random import randint
import time
from datetime import timedelta
from datetime import datetime

import numpy as np
import cv2 as cv

from django.db import models
from django.utils.html import mark_safe
from django.core.files.base import ContentFile


from creep_app.eye import Eye
from creep_app.window import Window
from creep_app.brain import Brain

logger = logging.getLogger(__name__)

class Screenshot(models.Model):
    image = models.ImageField(upload_to='images/')
    is_nsfw = models.BooleanField(default=None, null=True, blank=True)
    
    title = models.CharField(max_length=200,)
    exec_name = models.CharField(max_length=200,)

    keep = models.BooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image.name
    
    def image_tag(self):
        return mark_safe('<img src="/media/%s" width="300" />' % (self.image))

    class Meta:
        ordering = ['-created']
    
    @classmethod
    def snap(cls,eye : Eye, after_title_change: bool = False, after_stable_title : int | bool = False, max_wait: int = 60) -> None|np.ndarray:

        initial_window , max_wait = Window.waitForActiveWindow(max_wait)
        
        if initial_window == None:
            logger.warning("No initial_window found after %s seconds",max_wait)
            return None
        else:
            logger.info("Initial window found: %s",initial_window.title)
        
        if after_title_change != False:
            final_window , max_wait = Window.waitForActiveWindow(max_wait,invalid_title=initial_window.title)
            
            if final_window == None:
                logger.warning("No final_window found afer %s seconds",max_wait)
                return None
            else:
                logger.info("Final window found: %s",final_window.title)
        else:
            final_window = initial_window
        
        if after_stable_title != False:
            logger.info("Waiting %s seconds for stable title",after_stable_title)
            
            time.sleep(after_stable_title)
            stable_window , max_wait = Window.waitForActiveWindow(max_wait)
            
            if stable_window == None:
                logger.warning("No stable_window found after %s seconds",max_wait)
                return None
            
            if stable_window.title != final_window.title:
                logger.info("Stable window title does not match final window title")
                logger.info("Restarting snap with new max_wait: %s",max_wait)
                return cls.snap(after_title_change=after_title_change,after_stable_title=after_stable_title,max_wait=max_wait)
            else:
                logger.info("Window is stable")
        
        window_coordinates = final_window.get_coordinates()
        logger.info("Window coordinates: %s",window_coordinates)

        img = eye.snap(window_coordinates)

        return img , final_window.title , final_window.exec_name
    
    @classmethod
    def save_image(cls, img: np.ndarray,title:str,exec_name:str,keep=False) -> None:
        screenshot = cls()
        screenshot.image.save(f'{int(time.time())}.png', ContentFile(img))
        screenshot.keep = keep
        screenshot.title = title
        screenshot.exec_name = exec_name
        screenshot.save()
        return screenshot

    @classmethod
    def snap_active(cls,sleep_interval=0):
        """ Contantinously take screenshots of the active window """
        eye = Eye()
        while True:
            try:
                img, title, exec_name  = cls.snap(eye,after_title_change=True,after_stable_title=5)
            except:
                logger.exception("Unable to snap screenshot")
                eye = Eye()
                continue

            if img != None:
                cls.save_image(img,title,exec_name)

            time.sleep(sleep_interval)

    @classmethod
    def snap_random(cls,sleep_interval_min=0,sleep_interval_max = 60,keep=False):
        """ Contantinously take screenshots of the active window """
        eye = Eye()
        while True:
            try:
                img, title, exec_name = cls.snap(eye)
            except:
                logger.exception("Unable to snap screenshot")
                eye = Eye()
                continue

            if img != None:
                cls.save_image(img,title,exec_name,keep=keep)

            time.sleep(randint(sleep_interval_min,sleep_interval_max))

    @classmethod
    def run_detections(cls,splice=False):
        """Run NSFW Detection on all images"""
        brain = Brain()
        for screenshot in cls.objects.filter(is_nsfw=None):
            logger.info("Running NSFW Detection on %s",screenshot.title)

            if not screenshot.path.exists():
                logger.warning("Image file does not exist on disk")
                screenshot.delete()
                continue

            img = cv.imdecode(np.frombuffer(screenshot.image.read(), np.uint8), 1)
            if brain.detect(img)['is_nsfw']:
                screenshot.is_nsfw = True
            elif splice:
                spliced_images = brain.splice(img)
                for spliced_image in spliced_images:
                    if brain.detect(spliced_image)['is_nsfw']:
                        screenshot.is_nsfw = True
                        break
                    else:
                        screenshot.is_nsfw = False
            else:
                screenshot.is_nsfw = False

            logger.info("NSFW Detection result: %s",screenshot.is_nsfw)
            
            if screenshot.is_nsfw:
                screenshot.keep = True

            if not screenshot.keep:
                # Delete image from disk
                screenshot.image.delete()
                screenshot.delete()
            else:
                screenshot.save()

    @classmethod
    def clean(cls):
        """Delete all images older than 7 days"""
        for screenshot in cls.objects.filter(created__lte=datetime.now()-timedelta(days=7)):
            screenshot.image.delete()
            screenshot.delete()             
