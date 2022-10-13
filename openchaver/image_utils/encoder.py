import base64
import numpy as np
import cv2

def encode_numpy_to_base64(img: np.ndarray) -> str:
    """
    Encode a numpy array to base64.
    """
    return base64.b64encode(cv2.imencode('.png', img)[1]).decode()

def decode_base64_to_numpy(str: str) -> np.ndarray:
    """
    Decode a base64 string to a numpy array.
    """
    return cv2.imdecode(np.frombuffer(base64.b64decode(str), np.uint8), -1)