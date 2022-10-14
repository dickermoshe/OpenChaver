import logging

import numpy as np
import cv2 as cv

from .const import MODEL_PATH, CLASSIFICATION_MODEL_URL
from .utils import download_file

logger = logging.getLogger(__name__)

class OpenNsfw:
    def __init__(self):
        classify_model_path = MODEL_PATH / "open_nsfw.onnx"
        logger.debug(f"Loading classification model from {classify_model_path}")

        if not classify_model_path.exists():
            logger.debug(f"Downloading classification model from {CLASSIFICATION_MODEL_URL}")
            download_file(CLASSIFICATION_MODEL_URL,classify_model_path)

        self.lite_model = cv.dnn.readNet(str(classify_model_path))


    def classify(self, images: list[np.ndarray],threshold = 0.6):
        """Classify an image."""
        
        # Preprocess images
        # Copied from
        # https://pypi.org/project/opennsfw-standalone/
        preprocessed_images = []
        for image in images:

            image = cv.resize(image, (224, 224), interpolation=cv.INTER_LINEAR)

            image_jpeg_data = image.astype(np.float32, copy=False)

            image_jpeg_data -= np.array([104, 117, 123], dtype=np.float32)

            image_jpeg_data = np.expand_dims(image_jpeg_data, axis=0)

            preprocessed_images.append(image_jpeg_data)


        # Run model
        for image in preprocessed_images:
            self.lite_model.setInput(image)
            result = self.lite_model.forward()
            yield result[0][1] > threshold

    
    def is_nsfw(self, image: np.ndarray, threshold=0.6) -> bool:
        """Classify an image."""
        return next(self.classify([image], threshold))