import logging
import mss
import numpy as np

logger = logging.getLogger(__name__)
class Eye:
    def __init__(self,):

        try:
            logger.info("Initializing MSS")
            self.sct = mss.mss()
        except:
            logger.exception("Unable to initialize mss")


    def snap(self,coordinates):
        logger.info("Taking screenshot")
        try:
            shot = self.sct.grab(coordinates)
        except:
            logger.exception("Unable to take screenshot")
            return None
        
        try:
            img = np.array(shot)
        except:
            logger.exception("Unable to convert to numpy array")
            return None

        img = img[:,:,:3] # Remove alpha channel

        return img

