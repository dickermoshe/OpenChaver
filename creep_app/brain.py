import logging
import cv2 as cv
import numpy as np
from PIL import Image
import numpy as np
from io import BytesIO
from random import randint
from time import time
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

def read_image_bgr(image):
    """Read an image in BGR format.
    Args
        path: Path to the image.
    """
    image = np.ascontiguousarray(Image.fromarray(image))
    return image[:, :, ::-1]


def _preprocess_image(x):
    x = x.astype(np.float32)
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
    img = cv.resize(img, None, fx=scale, fy=scale)
    return img, scale


def preprocess_image(
    image_path,
    min_side,
    max_side,
):
    image = read_image_bgr(image_path)
    image = _preprocess_image(image)
    image, scale = resize_image(image, min_side=min_side, max_side=max_side)
    return image, scale

def color_in_image(img: np.ndarray) -> bool:
    """Check if the image has color"""
    return np.count_nonzero(img[:, :, 0] - img[:, :, 1]) > 0 or np.count_nonzero(
        img[:, :, 1] - img[:, :, 2]
    ) > 0

def splice_images(image, boring_shift=1, min_contour_area=1500, max_aspect_ratio=3,mser=False):
    """Splice Screenshot into a single images"""
    
    # Create a mask that only contains the colored pixels
    t = time()
    red, green, blue = cv.split(image)
    r_g = np.absolute(red - green)
    r_b = np.absolute(red - blue)
    g_b = np.absolute(green - blue)
    colored_pixels = r_g + r_b + g_b
    _, mask = cv.threshold(
        colored_pixels, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU
    )
    logger.debug(f"Time to create colored mask: {time() - t}")

    
    # Create a mask that only contains the mser pixels
    if mser or not color_in_image(image):
        t = time()
        mser = cv.MSER_create()
        regions, _ = mser.detectRegions(image)
        hulls = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]
        mser_mask = np.zeros((image.shape[0], image.shape[1], 1), dtype=np.uint8)
        for contour in hulls:
            if len(contour) > 2:
                # If contour is too small, ignore it
                if cv.contourArea(contour) < min_contour_area:
                    cv.drawContours(mser_mask, [contour], -1, (255, 255, 255), -1)
        mask = cv.bitwise_or(mask, mser_mask)
        logger.debug(f"Time to create mser mask: {time() - t}")


    # Create a mask of boring pixels
    t = time()
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    shift_r = np.roll(gray, boring_shift, axis=1)
    shift_l = np.roll(gray, boring_shift * -1, axis=1)
    shift_u = np.roll(gray, boring_shift, axis=0)
    shift_d = np.roll(gray, boring_shift * -1, axis=0)
    diff_r = np.absolute(gray - shift_r)
    diff_l = np.absolute(gray - shift_l)
    diff_u = np.absolute(gray - shift_u)
    diff_d = np.absolute(gray - shift_d)
    diff = diff_r * diff_l * diff_u * diff_d

    _, boring_mask = cv.threshold(diff, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)
    logger.debug(f"Time to create boring mask: {time() - t}")

    # Minus the boring pixels from the mask
    t = time()
    mask = cv.bitwise_and(mask, boring_mask)
    logger.debug(f"Time to remove boring pixels: {time() - t}")

    # morphologyEx
    t = time()
    kernel = np.ones((3, 3), np.uint8)
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=5)
    mask = cv.morphologyEx(mask, cv.MORPH_OPEN, kernel, iterations=5)
    logger.debug(f"Time to morphologyEx: {time() - t}")

    # Deblot
    t = time()
    nb_blobs, im_with_separated_blobs, stats, _ = cv.connectedComponentsWithStats(mask)
    sizes = stats[:, -1]
    sizes = sizes[1:]
    nb_blobs -= 1
    im_result = np.zeros((mask.shape))
    for blob in range(nb_blobs):
        if sizes[blob] >= 10000:
            im_result[im_with_separated_blobs == blob + 1] = 255
    mask = im_result.astype(np.uint8)
    logger.debug(f"Time to deblot: {time() - t}")

    # Mask the image
    t = time()
    masked_image = cv.bitwise_and(image, image, mask=mask)
    logger.debug(f"Time to mask image: {time() - t}")

    # Find bounding boxes
    t = time()
    gray = cv.cvtColor(masked_image, cv.COLOR_BGR2GRAY)
    contours, _ = cv.findContours(gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv.contourArea(c) > min_contour_area]
    bounding_boxes = []
    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        # If the images aspect ratio is very narrow or very wide, skip it
        if w / h > max_aspect_ratio or w / h < max_aspect_ratio * 0.1:
            continue
        bounding_boxes.append((x, y, w, h))
    logger.debug(f"Time to find bounding boxes: {time() - t}")

    # Remove overlapping bounding boxes
    t = time()
    filtered_boxes = []
    for box in bounding_boxes:
        x, y, w, h = box
        contained = False
        for box2 in bounding_boxes:
            x2, y2, w2, h2 = box2
            if x2 < x and y2 < y and x2 + w2 > x + w and y2 + h2 > y + h:
                contained = True
                break
        if not contained:
            filtered_boxes.append(box)
    logger.debug(f"Time to remove overlapping bounding boxes: {time() - t}")

    # Cut out the bounding boxes
    images = []
    for x, y, w, h in filtered_boxes:
        images.append(image[y : y + h, x : x + w])

    return images


def match_size(images: list[np.ndarray]) -> list[np.ndarray]:
    """Resize images to the size of the largest image by adding black borders"""
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


def skin_pixels(img: np.ndarray | list[np.ndarray], threshold=0.01) -> bool:

    if type(img) == list:
        if len(img) == 0:
            return False
        if len(img) == 1:
            img = img[0]
        else:
            img = match_size(img)
            img = np.concatenate(img, axis=1)

    # Amount of pixels in the image
    total_pixels = img.shape[0] * img.shape[1]
    threshold = total_pixels * threshold


    # Convert image to HSV
    img_copy = img.copy()
    blured = cv.GaussianBlur(img_copy, (5, 5), 0)

    min_HSV = np.array([0, 58, 30], dtype="uint8")
    max_HSV = np.array([33, 255, 255], dtype="uint8")

    imageHSV = cv.cvtColor(blured, cv.COLOR_BGR2HSV)
    skinRegionHSV = cv.inRange(imageHSV, min_HSV, max_HSV)

    return np.count_nonzero(skinRegionHSV) > threshold


class NudeNet:
    def __init__(self):
        from django.conf import settings
        import onnxruntime

        logger.debug("Initializing Detector")
        detection_model_path = (
            settings.BASE_DIR / "nsfw_model" / "detector_v2_default_checkpoint.onnx"
        )

        if not detection_model_path.exists():
            raise FileNotFoundError(f"Model file not found")

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
        fast=False,
        batch_size=5,
        test_mode=False,
    ) -> list[dict]:
        """Detect objects in an image."""

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
            scores = [op for op in outputs if isinstance(op[0][0], np.float32)][0]
            boxes = [op for op in outputs if isinstance(op[0][0], np.ndarray)][0]
            boxes /= scale

            for frame_boxes, frame_scores, frame_labels in zip(
                boxes,
                scores,
                labels,
            ):
                frame_result = {
                    "detections": [],
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

                frame_result["is_nsfw"] = self._eval_detection(
                    frame_result["detections"]
                )
                results.append(frame_result)

        if test_mode:
            for i, result in enumerate(results):
                if result["is_nsfw"]:
                    img = images[i]
                    for detection in result["detections"]:
                        box = detection["box"]
                        cv.rectangle(
                            img, (box[0], box[1]), (box[2], box[3]), (0, 0, 255), 2
                        )

        return results

    def _eval_detection(self, result, threshold=0.5) -> bool:
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

class OpenNsfw:
    def __init__(self):
        from django.conf import settings
        import onnxruntime

        logger.debug("Initializing Detector")
        classify_model_path = settings.BASE_DIR / "nsfw_model" / "open-nsfw.onnx"

        if not classify_model_path.exists():
            raise FileNotFoundError(f"Model file not found")

        self.classify_model = onnxruntime.InferenceSession(
            str(classify_model_path), providers=["CPUExecutionProvider"]
        )


    def classify(self, images: list[np.ndarray],threshold = 0.6) -> list[dict]:
        """Classify an image."""
        # convert cv2 images bytes object
        preprocessed_images = []
    
        for image in images:
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            image = Image.fromarray(image)

            
            if image.mode != "RGB":
                image = image.convert("RGB")
            
            image = image.resize((256, 256), resample=Image.BILINEAR)

            cropped_size = 224
            image_width, image_height = image.size
            image = image.crop(
                (
                    (image_width - cropped_size) / 2,
                    (image_height - cropped_size) / 2,
                    (image_width + cropped_size) / 2,
                    (image_height + cropped_size) / 2,
                )
            )
            with BytesIO() as jpeg_buffer:
                image.save(jpeg_buffer, format="JPEG")
                jpeg_buffer.seek(0)

                image_jpeg_data = np.array(Image.open(jpeg_buffer), dtype=np.float32, copy=False)

            image_jpeg_data = image_jpeg_data[:, :, ::-1]

            image_jpeg_data -= np.array([104, 117, 123], dtype=np.float32)

            image_jpeg_data = np.expand_dims(image_jpeg_data, axis=0)

            preprocessed_images.append(image_jpeg_data)


        # Run the model
        for image in preprocessed_images:
            input_name = self.classify_model.get_inputs()[0].name
            outputs = [output.name for output in self.classify_model.get_outputs()]
            result = self.classify_model.run(outputs, {input_name: image})
            yield result[0][0][1] > threshold
    
    def is_nsfw(self, image: np.ndarray, threshold=0.6) -> bool:
        """Classify an image."""
        return next(self.classify([image], threshold))


