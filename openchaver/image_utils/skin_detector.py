#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'Will Brennan'

import logging
import cv2
import numpy as np
from .deblot import deblot

logger = logging.getLogger(__name__)


def count_skin_pixels(image:np.ndarray):
    """Count the number of pixels in the image which are skin colored"""
    logger.debug("counting skin pixels")
    
    lower = np.array([0, 48, 80], dtype = "uint8")
    upper = np.array([20, 255, 255], dtype = "uint8")
    converted = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
    skinMask = cv2.inRange(converted, lower, upper)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    skinMask = cv2.erode(skinMask, kernel, iterations = 2)
    skinMask = cv2.dilate(skinMask, kernel, iterations = 2)
    skinMask = deblot(skinMask, 250)
    return np.sum(skinMask)

def color_in_image(img: np.ndarray) -> bool:
    """Check if the image has color"""
    return np.count_nonzero(img[:, :, 0] - img[:, :, 1]) > 0 or np.count_nonzero(
        img[:, :, 1] - img[:, :, 2]
    ) > 0


def contains_skin(img:np.ndarray, thresh=1.5):
    logger.debug("checking if image contains skin")

    
    
    # Return True if the image is completely black and white
    color = color_in_image(img)
    logger.debug(f"B&W: {not color}")
    if not color:
        return True
    
    skin_pixel_count = count_skin_pixels(img)  
    skin_ratio = skin_pixel_count / (img.shape[0] * img.shape[1])
    logger.debug(f"Skin ratio: {skin_ratio}")
    return skin_ratio > thresh