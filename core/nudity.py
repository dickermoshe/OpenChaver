import logging
from pathlib import Path

import numpy as np
from PIL import Image
import cv2 as cv

from openchaver.dirs import get_data_dir
from .image_utils import match_size, resize_image


model_dir = get_data_dir() / "models"
model_dir.mkdir(parents=True, exist_ok=True)

DETECTION_MODEL_URL = 'https://pub-43a5d92b0b0b4908a9aec2a745986a23.r2.dev/detector_v2_default_checkpoint.onnx'  # noqa: E501
DETECTION_MODEL_SHA256_HASH = "D4BE1C504BE61851D9745E6DA8FA09455EB39B8856626DD6B5CA413C9E8B1578"  # noqa: E501
DETECTION_MODEL_PATH = model_dir / 'detect.onnx'

CLASSIFICATION_MODEL_URL = 'https://pub-43a5d92b0b0b4908a9aec2a745986a23.r2.dev/open-nsfw.onnx'  # noqa: E501
CLASSIFICATION_MODEL_SHA256_HASH = "864BB37BF8863564B87EB330AB8C785A79A773F4E7C43CB96DB52ED8611305FA"  # noqa: E501
CLASSIFICATION_MODEL_PATH = model_dir / 'classify.onnx'

logger = logging.getLogger(__name__)

def test_model(model_path: Path) -> bool:
    """Test if a model can be loaded"""
    import onnxruntime
    try:
        onnxruntime.InferenceSession(str(model_path),
                                     providers=["CPUExecutionProvider"])
        return True
    except:  # noqa E722
        logger.error("Failed to load model")
        return False

def chech_hash(path: Path, hash: str) -> bool:
    """Check the hash of a file"""
    import hashlib
    if not path.exists():
        return False
    with open(path, "rb") as f:
        file_hash = hashlib.sha256()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest().upper() == hash

def download_model(url, path: Path, hash=None):
    """Download the model"""
    import requests

    logger.info("Downloading model...")
    try:
        # Download
        response = requests.get(url, stream=True, verify=False)
        with open(path, "wb") as handle:
            for data in response.iter_content(chunk_size=8192):
                handle.write(data)

        # Check hash
        if hash:
            if not chech_hash(path, hash):
                raise Exception("Hash mismatch")

        # Test Load model
        if not test_model(path):
            raise Exception("Failed to load model")

    except:  # noqa E722
        logger.error("Failed to download model")
        path.unlink(missing_ok=True)
        raise

class Detector:

    def __init__(self):
        import onnxruntime
        model_file = DETECTION_MODEL_PATH
        logger.info(f"Loading detection model from {model_file}")

        if not model_file.exists():
            logger.info(
                f"Downloading detection model from {DETECTION_MODEL_URL}")
            download_model(DETECTION_MODEL_URL, model_file,
                           DETECTION_MODEL_SHA256_HASH)

        self.detection_model = onnxruntime.InferenceSession(
            str(model_file), providers=["CPUExecutionProvider"])

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
            image = np.ascontiguousarray(
                Image.fromarray(image_path))[:, :, ::-1]
            image = image.astype(np.float32)
            image -= [103.939, 116.779, 123.68]
            image, scale = resize_image(image,
                                        min_side=min_side,
                                        max_side=max_side)
            return image, scale

        # Match size
        images = match_size(images)

        # Preprocess images
        preprocessed_images = [
            preprocess_image(img,
                             min_side=480 if fast else 800,
                             max_side=800 if fast else 1333) for img in images
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
            scores = [
                op for op in outputs if isinstance(op[0][0], np.float32)
            ][0]  # type: ignore
            boxes = [op for op in outputs
                     if isinstance(op[0][0], np.ndarray)][0]
            boxes /= scale

            for frame_boxes, frame_scores, frame_labels in zip(
                    boxes,
                    scores,
                    labels,
            ):
                frame_result = {"detections": [], 'is_nsfw': False}
                for box, score, label in zip(frame_boxes, frame_scores,
                                             frame_labels):
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
            if detection[
                    "label"] in nsfw_labels and detection["score"] > threshold:
                return True
        return False

    def is_nsfw(self, img: np.ndarray) -> dict:
        """Detect objects in an image."""
        return self.detect([img])[0]

class Classifier:

    def __init__(self):
        model_file = CLASSIFICATION_MODEL_PATH
        logger.info(f"Loading classification model from {model_file}")

        if not model_file.exists():
            logger.info(
                f"Downloading classification model from {CLASSIFICATION_MODEL_URL}"  # noqa: E501
            )
            download_model(CLASSIFICATION_MODEL_URL, model_file,
                           CLASSIFICATION_MODEL_SHA256_HASH)

        self.lite_model = cv.dnn.readNet(str(model_file))

    def classify(self, images: list[np.ndarray], threshold=0.6):
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