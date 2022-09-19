import logging

import onnxruntime
import cv2
import numpy as np
from PIL import Image

from creep import script_location

logger = logging.getLogger(__name__)




def read_image_bgr(image):
    """ Read an image in BGR format.
    Args
        path: Path to the image.
    """
    path = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    image = np.ascontiguousarray(Image.fromarray(image))

    return image[:, :, ::-1]


def _preprocess_image(x, mode="caffe"):
    x = x.astype(np.float32)

    if mode == "tf":
        x /= 127.5
        x -= 1.0
    elif mode == "caffe":
        x -= [103.939, 116.779, 123.68]

    return x


def compute_resize_scale(image_shape, min_side=800, max_side=1333):
    (rows, cols, _) = image_shape

    smallest_side = min(rows, cols)

    scale = min_side / smallest_side

    largest_side = max(rows, cols)
    if largest_side * scale > max_side:
        scale = max_side / largest_side

    return scale


def resize_image(img, min_side=800, max_side=1333):
    scale = compute_resize_scale(img.shape, min_side=min_side, max_side=max_side)

    img = cv2.resize(img, None, fx=scale, fy=scale)

    return img, scale


def preprocess_image(
    image_path, min_side=800, max_side=1333,
):
    image = read_image_bgr(image_path)
    image = _preprocess_image(image)
    image, scale = resize_image(image, min_side=min_side, max_side=max_side)
    return image, scale

class Detector:
    def __init__(self) -> None:
        logger.debug("Initializing Detector")
        model_path = script_location / "models" / "detector_v2_default_checkpoint.onnx"

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        

        self.detection_model = onnxruntime.InferenceSession(str(model_path),providers=['CPUExecutionProvider'])
        self.classes = ['EXPOSED_ANUS', 'EXPOSED_ARMPITS', 'COVERED_BELLY', 'EXPOSED_BELLY', 'COVERED_BUTTOCKS', 'EXPOSED_BUTTOCKS', 'FACE_F', 'FACE_M', 'COVERED_FEET',
                        'EXPOSED_FEET', 'COVERED_BREAST_F', 'EXPOSED_BREAST_F', 'COVERED_GENITALIA_F', 'EXPOSED_GENITALIA_F', 'EXPOSED_BREAST_M', 'EXPOSED_GENITALIA_M']

    def detect(self, img, mode="default", min_prob=None):
        if mode == "fast":
            image, scale = preprocess_image(img, min_side=480, max_side=800)
            if not min_prob:
                min_prob = 0.5
        else:
            image, scale = preprocess_image(img)
            if not min_prob:
                min_prob = 0.6

        outputs = self.detection_model.run(
            [s_i.name for s_i in self.detection_model.get_outputs()],
            {self.detection_model.get_inputs()[0].name: np.expand_dims(image, axis=0)},
        )

        labels = [op for op in outputs if op.dtype == "int32"][0]
        scores = [op for op in outputs if isinstance(op[0][0], np.float32)][0]
        boxes = [op for op in outputs if isinstance(op[0][0], np.ndarray)][0]

        boxes /= scale
        processed_boxes = []
        for box, score, label in zip(boxes[0], scores[0], labels[0]):
            if score < min_prob:
                continue
            box = box.astype(int).tolist()
            label = self.classes[label]
            processed_boxes.append(
                {"box": [int(c) for c in box], "score": float(score), "label": label}
            )

        return processed_boxes