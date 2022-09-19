import logging

from .brain import Brain
from .eye import Eye
from .window import Window

import cv2 as cv
import numpy as np
import time

logger = logging.getLogger(__name__)


class Heart:
    def __init__(self) -> None:
        self.brain = Brain()
        self.eye = Eye()

    def test_brain(self):
        try:
            # Create a random image 1920 x 1080
            img = np.random.randint(0, 255, (1080, 1920, 3), dtype=np.uint8)

            # Composite a red and green rectangle on the image
            cv.rectangle(img, (200, 200), (100, 100), (0, 255, 0), -1)
            cv.rectangle(img, (500, 500), (200, 100), (0, 0, 255), -1)

            # Splice image
            imgs = self.brain.splice(img)

            # Run detection
            for img in imgs:
                self.brain.detect(img)
            return True
        except:
            logger.exception("Test failed")
            return False

    def test_eye(self):
        try:
            img = self.eye.snap((
                0,
                0,
                1920,
                1080
            ))
            return img != None
        except:
            logger.exception("Test failed")
            return False

    def snap(self, after_title_change: bool = False, after_stable_title : int | bool =False, max_wait: int = 60) -> None|np.ndarray:

        initial_window , max_wait = Window.waitForActiveWindow(max_wait)
        
        if initial_window == None:
            logger.error("No initial_window found")
            return None
        
        if after_title_change != False:
            final_window , max_wait = Window.waitForActiveWindow(max_wait,invalid_title=initial_window.title)
            
            if final_window == None:
                logger.error("No final_window found")
                return None
        else:
            final_window = initial_window
        
        if after_stable_title != False:
            time.sleep(after_stable_title)
            stable_window , max_wait = Window.waitForActiveWindow(max_wait)
            
            if stable_window == None:
                logger.error("No stable_window found")
                return None
            
            if stable_window.title != final_window.title:
                return self.snap(after_title_change=after_title_change,after_stable_title=after_stable_title,max_wait=max_wait)
        
        img = self.eye.snap(final_window.get_coordinates())

        return img