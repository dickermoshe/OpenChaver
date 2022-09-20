import logging
from random import randint
import time
from datetime import timedelta
from datetime import datetime
from pathlib import Path

import psutil
import numpy as np
import cv2 as cv

from django.db import models
from django.utils.html import mark_safe
from django.core.files.base import ContentFile


from creep_app.eye import Eye
from creep_app.window import Window
from creep_app.brain import Brain

logger = logging.getLogger('django')

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
    def snap(cls, eye : Eye, after_title_change: bool = False, after_stable_title : int | bool = False,initial_window = None ,max_wait: int = 60) -> None|np.ndarray:
        
        if initial_window is None:
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
                return cls.snap(eye,after_title_change=after_title_change,after_stable_title=after_stable_title,max_wait=max_wait,initial_window=stable_window)
            else:
                logger.info("Window is stable")
        
        window_coordinates = final_window.get_coordinates()
        logger.info("Window coordinates: %s",window_coordinates)

        img = eye.snap(window_coordinates)

        return img , final_window.title , final_window.exec_name
    
    @classmethod
    def save_image(cls, img: np.ndarray,title:str,exec_name:str,keep=False) :
        screenshot = cls()
        
        # Only save the image if it contains skin pixels
        # However due to a simple Black and White Filter bypass we only do this 9/10 times
        if randint(0,9) != 0 and keep == False:
            logger.info("Checking if image contains skin pixels")
            img_copy = img.copy()
            blured = cv.GaussianBlur(img_copy,(5,5),0)

            min_HSV = np.array([0, 58, 30], dtype = "uint8")
            max_HSV = np.array([33, 255, 255], dtype = "uint8")

            imageHSV = cv.cvtColor(blured, cv.COLOR_BGR2HSV)
            skinRegionHSV = cv.inRange(imageHSV, min_HSV, max_HSV)
            
            if np.count_nonzero(skinRegionHSV) == 0:
                logger.info("Image does not contain skin pixels")
                return None

        logger.info("Saving image")
          
        _, buffer = cv.imencode('.png', img)
        screenshot.image.save(f'{int(time.time())}.png', ContentFile(buffer))
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

            if img is not None:
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
    def run_detections(cls,batch_size=10):
        """Run NSFW Detection on all images"""

        brain = Brain()
        screenshots = cls.objects.filter(is_nsfw=None)

        # Run detection if one following conditions are met
        # 1. There are more than 10 images to be processed
        # 2. CPU usage is below 50%

        if len(screenshots) < 10 and psutil.cpu_percent() > 50:
            return


        for screenshot in screenshots:
            logger.info("Removing non-existant records on %s",screenshot.title)

            if not Path(screenshot.image.path).exists():
                logger.warning("Image file does not exist on disk")
                screenshot.delete()
                continue
        
        screenshots = cls.objects.filter(is_nsfw=None)
        
        screenshot_groups = {}
        
        for screenshot in screenshots:
            image_width = screenshot.image.width
            image_height = screenshot.image.height
            image_size = f'{image_width}x{image_height}'
            if image_size not in screenshot_groups:
                screenshot_groups[image_size] = []
            screenshot_groups[image_size].append(screenshot)

        batches = []
        for images in screenshot_groups.values():
            # Add in batches of batch_size
            for i in range(0, len(images), batch_size):
                batches.append(images[i:i + batch_size])

        for b in batches:
            images = []
            for screenshot in b:
                img = cv.imread(screenshot.image.path)
                images.append(img)

            if brain.detect(images)['is_nsfw']:
                for i in len(images):
                    if brain.detect(images[i])['is_nsfw']:
                        b[i].is_nsfw = True
                    else:
                        b[i].is_nsfw = False
                    b[i].save()
            else:
                for screenshot in b:
                    screenshot.is_nsfw = False
                    screenshot.save()
        
        # Delete all images that are not marked as keep and is_nsfw is not none
        cls.objects.filter(keep=False,is_nsfw__isnull=False).delete()

                    


    @classmethod
    def clean(cls):
        """Delete all images older than 7 days"""
        for screenshot in cls.objects.filter(created__lte=datetime.now()-timedelta(days=7)):
            screenshot.image.delete()
            screenshot.delete()             
