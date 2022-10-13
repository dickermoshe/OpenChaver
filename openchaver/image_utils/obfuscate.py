import cv2 as cv 
import numpy as np
def pixelate(img, scale =.2,max_width_return = 512):
    """
    Pixelate an image to hide text.
    """
    image = cv.resize(img, (0, 0), fx=scale, fy=scale)
    image = cv.resize(image, (max_width_return, int(image.shape[0] * max_width_return / image.shape[1])))
    return image

def blur(img):
    """
    Blur image to hide innapropriate content.
    return 2 images, one blurred and very blurred
    """
    low_blur = cv.blur(img, (5, 5))
    high_blur = cv.blur(img, (9, 9))
    return low_blur, high_blur

def obfuscate_image(image: np.ndarray) -> bytes:
    """
    Obfuscate an image to hide innapropriate content.

    """
    # Pixelate
    image = pixelate(image)

    return image


    