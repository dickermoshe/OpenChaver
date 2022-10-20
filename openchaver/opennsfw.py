import logging

import numpy as np
import cv2 as cv

from .const import MODEL_DIR, CLASSIFICATION_MODEL_URL , CLASSIFICATION_MODEL_SHA256_HASH
from .utils import download_model

logger = logging.getLogger(__name__)

class OpenNsfw:
    def __init__(self):
        model_file = MODEL_DIR / "open_nsfw.onnx"
        logger.info(f"Loading classification model from {model_file}")

        if not model_file.exists():
            logger.info(f"Downloading classification model from {CLASSIFICATION_MODEL_URL}")
            download_model(CLASSIFICATION_MODEL_URL,model_file,CLASSIFICATION_MODEL_SHA256_HASH)

        self.lite_model = cv.dnn.readNet(str(model_file))



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