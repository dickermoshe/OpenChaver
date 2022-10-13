# Imports
import logging
from pathlib import Path

import cv2 as cv
import numpy as np
from PIL import Image


from . import DATA_DIR
from .image_utils.resize import *

MODEL_PATH = DATA_DIR / "nsfw_model"
if not MODEL_PATH.exists():
    MODEL_PATH.mkdir(parents=True)

# Logging
logger = logging.getLogger(__name__)

def download_model(url,path:Path):
    """Download the model"""
    import requests

    # Download the model in chunks
    logger.info("Downloading model")
    try:
        response = requests.get(url, stream=True)
        with open(path, "wb") as handle:
            for data in response.iter_content(chunk_size=8192):
                handle.write(data)
        logger.info("Downloaded model")
    except:
        logger.error("Failed to download model")
        if (path).exists():
            (path).unlink()
        raise


class NudeNet:
    def __init__(self):
        import onnxruntime
        logger.debug("Initializing Detector...")

        detection_model_path = (
            MODEL_PATH / "nude_net.onnx"
        )
        logger.debug(f"Loading detection model from {detection_model_path}")
        if not detection_model_path.exists():
            download_model('https://pub-43a5d92b0b0b4908a9aec2a745986a23.r2.dev/detector_v2_default_checkpoint.onnx',detection_model_path)

        self.detection_model = onnxruntime.InferenceSession(
            str(detection_model_path), providers=["CPUExecutionProvider"]
        )

        self.classes = [
            "EXPOSED_ANUS",
            "EXPOSED_ARMPITS",
            "COVERED_BELLY",
            "EXPOSED_BELLY",
            "COVERED_BUTTOCKS",
            "EXPOSED_BUTTOCKS",
            "FACE_F",
            "FACE_M",
            "COVERED_FEET",
            "EXPOSED_FEET",
            "COVERED_BREAST_F",
            "EXPOSED_BREAST_F",
            "COVERED_GENITALIA_F",
            "EXPOSED_GENITALIA_F",
            "EXPOSED_BREAST_M",
            "EXPOSED_GENITALIA_M",
        ]

    def detect(
        self,
        images: list[np.ndarray],
        min_prob=None,
        fast=True,
        batch_size=5,
    ) -> list[dict]:
        """Detect objects in an image."""
        # Function to preprocess the image
        def preprocess_image(
            image_path,
            min_side,
            max_side,
        ):
            image = np.ascontiguousarray(Image.fromarray(image_path))[:, :, ::-1]
            image = image.astype(np.float32)
            image -= [103.939, 116.779, 123.68]
            image, scale = resize_image(image, min_side=min_side, max_side=max_side)
            return image, scale

        # Match size
        images = match_size(images)

        # Preprocess images
        preprocessed_images = [
            preprocess_image(
                img, min_side=480 if fast else 800, max_side=800 if fast else 1333
            )
            for img in images
        ]
        # Show images

        min_prob = 0.5 if fast else 0.6
        scale = preprocessed_images[0][1]
        preprocessed_images = [p[0] for p in preprocessed_images]
        results = []

        while len(preprocessed_images):
            batch = preprocessed_images[:batch_size]
            preprocessed_images = preprocessed_images[batch_size:]
            outputs = self.detection_model.run(
                [s_i.name for s_i in self.detection_model.get_outputs()],
                {self.detection_model.get_inputs()[0].name: np.asarray(batch)},
            )

            labels = [op for op in outputs if op.dtype == "int32"][0]
            scores = [op for op in outputs if isinstance(op[0][0], np.float32)][0]  # type: ignore
            boxes = [op for op in outputs if isinstance(op[0][0], np.ndarray)][0]
            boxes /= scale

            for frame_boxes, frame_scores, frame_labels in zip(
                boxes,
                scores,
                labels,
            ):
                frame_result = {
                    "detections": [],
                    'is_nsfw':False
                }
                for box, score, label in zip(frame_boxes, frame_scores, frame_labels):
                    if score < min_prob:
                        continue
                    box = box.astype(int).tolist()
                    label = self.classes[label]
                    detection = {
                        "box": [int(c) for c in box],
                        "score": float(score),
                        "label": label,
                    }
                    frame_result["detections"].append(detection)

                
                is_nsfw = self._eval_detection(frame_result["detections"])
                frame_result["is_nsfw"] = is_nsfw
                results.append(frame_result)

        return results

    def _eval_detection(self, result, threshold=0.6) -> bool:
        nsfw_labels = [
            "EXPOSED_ANUS",
            "EXPOSED_BUTTOCKS",
            "EXPOSED_BREAST_F",
            "EXPOSED_GENITALIA_F",
            "EXPOSED_GENITALIA_M",
        ]
        for detection in result:
            if detection["label"] in nsfw_labels and detection["score"] > threshold:
                return True
        return False

    def is_nsfw(self, img: np.ndarray) -> dict:
        """Detect objects in an image."""
        return self.detect([img])[0]

class OpenNsfw:
    def __init__(self):
        logger.debug("Initializing Detector")
        classify_model_path = MODEL_PATH / "open_nsfw.onnx"

        logger.debug(f"Loading classification model from {classify_model_path}")
        if not classify_model_path.exists():
            download_model('https://pub-43a5d92b0b0b4908a9aec2a745986a23.r2.dev/open-nsfw.onnx',classify_model_path)

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



            
        

