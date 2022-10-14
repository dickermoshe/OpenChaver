import logging
from pathlib import Path
import numpy as np
logger = logging.getLogger(__name__)

def is_frozen():
    """Check if the program is frozen by PyInstaller or Nuitka"""
    import sys
    pyinstaller = getattr(sys, 'frozen', False)
    nuitka = "__compiled__" in globals()
    logger.debug(f"Pyinstaller: {pyinstaller}, Nuitka: {nuitka}")
    return pyinstaller or nuitka

def chmod(path:str|Path):
    """Change file permissions"""
    import stat
    import oschmod
    oschmod.set_mode(str(path), stat.S_IRUSR | stat.S_IWUSR | stat.S_IXUSR)
    logger.debug(f"Changed permissions on {path}")

def obfuscate_text(text:str):
    """Obfuscate text by replaceing each character with the char next to it in the alphabet"""
    import string
    a = string.ascii_letters
    b = string.ascii_letters[-1] + string.ascii_letters[:-1]
    table = str.maketrans(a, b)
    return text.translate(table)

def reverse_obfuscate_text(text:str):
    """Reverse the obfuscation of text"""
    import string
    b = string.ascii_letters
    a = string.ascii_letters[-1] + string.ascii_letters[:-1]
    table = str.maketrans(a, b)
    return text.translate(table)


def obfuscate_image(img, scale =.2,max_width_return = 512):
    """
    Pixelate an image to hide text.
    """
    import cv2 as cv 
    image = cv.resize(img, (0, 0), fx=scale, fy=scale)
    image = cv.resize(image, (max_width_return, int(image.shape[0] * max_width_return / image.shape[1])))
    return image

def encode_numpy_to_base64(img:np.ndarray) -> str:
    """
    Encode a numpy array to base64.
    """
    import cv2 as cv
    import base64
    return base64.b64encode(cv.imencode('.png', img)[1]).decode()

def decode_base64_to_numpy(str: str) -> np.ndarray:
    """
    Decode a base64 string to a numpy array.
    """
    import cv2 as cv
    import base64
    return cv.imdecode(np.frombuffer(base64.b64decode(str), np.uint8), -1)

def download_file(url,path:Path):
    """Download the model"""
    import requests

    # Download the model in chunks
    logger.info("Downloading model...")
    try:
        response = requests.get(url, stream=True,verify=False)
        with open(path, "wb") as handle:
            for data in response.iter_content(chunk_size=8192):
                handle.write(data)
        chmod(path)
        logger.info("Model downloaded")
    except:
        logger.error("Failed to download model")
        if (path).exists():
            (path).unlink()
        raise

def compute_resize_scale(image_shape, min_side=800, max_side=1333):
    """Compute the scale to resize an image to a given size"""
    (rows, cols, _) = image_shape
    smallest_side = min(rows, cols)
    scale = min_side / smallest_side
    largest_side = max(rows, cols)
    if largest_side * scale > max_side:
        scale = max_side / largest_side
    return scale


def resize_image(img, min_side=800, max_side=1333):
    """Resize an image"""
    import cv2 as cv
    scale = compute_resize_scale(img.shape, min_side=min_side, max_side=max_side)
    img = cv.resize(img, None, fx=scale, fy=scale)
    return img, scale


def match_size(images: list[np.ndarray]) -> list[np.ndarray]:
    """Resize images to the size of the largest image by adding black borders"""
    import cv2 as cv
    max_width = max([img.shape[1] for img in images])
    max_height = max([img.shape[0] for img in images])
    resized_images = []
    for img in images:
        if img.shape[1] < max_width or img.shape[0] < max_height:
            resized_images.append(
                cv.copyMakeBorder(
                    img,
                    0,
                    max_height - img.shape[0],
                    0,
                    max_width - img.shape[1],
                    cv.BORDER_CONSTANT,
                    value=[0, 0, 0],
                )
            )
        else:
            resized_images.append(img)
    return resized_images

def is_profane(s:str) -> bool:
    import re
    from .const import BAD_WORDS
    if re.compile(r"\b" + r"\b|".join(BAD_WORDS)+r"\b",re.IGNORECASE,).search(s):
        return True
    else:
        return False

def deblot_image(mask:np.ndarray,min_size:float):
    """Remove small blobs from an image."""
    import cv2 as cv
    nb_blobs, im_with_separated_blobs, stats, _ = cv.connectedComponentsWithStats(
        mask)
    sizes = stats[:, -1]
    sizes = sizes[1:]
    nb_blobs -= 1
    im_result = np.zeros((mask.shape))
    for blob in range(nb_blobs):
        if sizes[blob] >= min_size:
            im_result[im_with_separated_blobs == blob + 1] = 255
    mask = im_result.astype(np.uint8)
    return mask

def count_skin_pixels(image:np.ndarray):
    """Count the number of pixels in the image which are skin colored"""
    import cv2 as cv
    
    lower = np.array([0, 48, 80], dtype = "uint8")
    upper = np.array([20, 255, 255], dtype = "uint8")
    converted = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    skinMask = cv.inRange(converted, lower, upper)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (11, 11))
    skinMask = cv.erode(skinMask, kernel, iterations = 2)
    skinMask = cv.dilate(skinMask, kernel, iterations = 2)
    skinMask = deblot_image(skinMask, 250)
    return np.sum(skinMask)

def color_in_image(img: np.ndarray) -> bool:
    """Check if the image has color"""
    return np.count_nonzero(img[:, :, 0] - img[:, :, 1]) > 0 or np.count_nonzero(
        img[:, :, 1] - img[:, :, 2]
    ) > 0


def contains_skin(img:np.ndarray, thresh=1.5) -> bool:
    """Check if the image contains skin beyond a certain threshold"""
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