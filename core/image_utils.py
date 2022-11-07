import logging

import cv2 as cv
import base64
import numpy as np

logger = logging.getLogger(__name__)


def encode_numpy_to_base64(img: np.ndarray) -> str:
    """
    Encode a numpy array to base64.
    """

    return base64.b64encode(cv.imencode(".png", img)[1]).decode()


def decode_base64_to_numpy(str: str) -> np.ndarray:
    """
    Decode a base64 string to a numpy array.
    """

    return cv.imdecode(np.frombuffer(base64.b64decode(str), np.uint8), -1)

def numpy_to_png_bytes(img: np.ndarray) -> bytes:
    """Convert a numpy array to a png image"""
    import cv2 as cv
    _, buffer = cv.imencode(".png", img)
    return buffer.tobytes()

def png_bytes_to_numpy(img_bytes: bytes) -> np.ndarray:
    """Convert a png image to a numpy array"""
    import cv2 as cv
    return cv.imdecode(np.frombuffer(img_bytes, np.uint8), -1)

def open_image(path: str) -> np.ndarray:
    """Open an image from a path"""
    return cv.imread(path)

def color_in_image(img: np.ndarray) -> bool:
    """Check if the image has color"""
    return (
        np.count_nonzero(img[:, :, 0] - img[:, :, 1]) > 0
        or np.count_nonzero(img[:, :, 1] - img[:, :, 2]) > 0
    )


def deblot_image(mask: np.ndarray, min_size: float):
    """Remove small blobs from an image."""
    import cv2 as cv

    (
        nb_blobs,
        im_with_separated_blobs,
        stats,
        _,
    ) = cv.connectedComponentsWithStats(  # noqa E501
        mask
    )
    sizes = stats[:, -1]
    sizes = sizes[1:]
    nb_blobs -= 1
    im_result = np.zeros((mask.shape))
    for blob in range(nb_blobs):
        if sizes[blob] >= min_size:
            im_result[im_with_separated_blobs == blob + 1] = 255
    mask = im_result.astype(np.uint8)
    return mask


def count_skin_pixels(image: np.ndarray):
    """Count the number of pixels in the image which are skin colored"""
    import cv2 as cv

    lower = np.array([0, 48, 80], dtype="uint8")
    upper = np.array([20, 255, 255], dtype="uint8")
    converted = cv.cvtColor(image, cv.COLOR_BGR2HSV)
    skin_mask = cv.inRange(converted, lower, upper)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (11, 11))
    skin_mask = cv.erode(skin_mask, kernel, iterations=2)
    skin_mask = cv.dilate(skin_mask, kernel, iterations=2)
    skin_mask = deblot_image(skin_mask, 250)
    return np.sum(skin_mask)


def contains_skin(img: np.ndarray, thresh=1.5) -> bool:
    """Check if the image contains skin beyond a certain threshold"""
    logger.info("checking if image contains skin")

    # Return True if the image is completely black and white
    color = color_in_image(img)
    logger.info(f"B&W: {not color}")
    if not color:
        return True

    skin_pixel_count = count_skin_pixels(img)
    skin_ratio = skin_pixel_count / (img.shape[0] * img.shape[1])
    logger.info(f"Skin ratio: {skin_ratio}")
    return skin_ratio > thresh


def get_bounding_boxes(image: np.ndarray) -> list:
    # Check if there are skin pixels in the image
    # This is done to remove images that are definitely not NSFW
    if not contains_skin(image, thresh=0.5):
        logger.info("Image does not contain skin. Skipping...")
        return []

    # Remove all parts of the image that are
    # very similar to their neighbors
    gray = cv.cvtColor(image, cv.COLOR_BGR2GRAY)
    shift_r = np.roll(gray, 1, axis=1)
    shift_l = np.roll(gray, 1 * -1, axis=1)
    shift_u = np.roll(gray, 1, axis=0)
    shift_d = np.roll(gray, 1 * -1, axis=0)
    diff_r = np.absolute(gray - shift_r)
    diff_l = np.absolute(gray - shift_l)
    diff_u = np.absolute(gray - shift_u)
    diff_d = np.absolute(gray - shift_d)
    diff = diff_r * diff_l * diff_u * diff_d
    _, mask = cv.threshold(diff, 0, 255, cv.THRESH_BINARY + cv.THRESH_OTSU)

    # Kernel for morphological operations
    # Relative to the size of the image
    kernel_size = int(image.shape[0] * 0.005)
    kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE, (kernel_size, kernel_size))

    # Morphological operations on the mask
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

    # Deblot the mask
    min_size = 0.0025 * mask.shape[0] * mask.shape[1]
    mask = deblot_image(mask, min_size=min_size)

    # Morphological operations on the mask
    mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

    # Apply the mask to the image
    masked_image = cv.bitwise_and(image, image, mask=mask)

    # Detect individual images
    max_aspect_ratio = 3
    gray = cv.cvtColor(masked_image, cv.COLOR_BGR2GRAY)
    contours, _ = cv.findContours(gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
    contours = [c for c in contours if cv.contourArea(c) > min_size]
    bounding_boxes = []
    for cnt in contours:
        x, y, w, h = cv.boundingRect(cnt)
        # If the images aspect ratio is very narrow or very wide, skip it
        if w / h > max_aspect_ratio or w / h < max_aspect_ratio * 0.1:
            continue
        bounding_boxes.append((x, y, w, h))

    filtered_bounding_boxes = []  # Images with a skin ratio above 5

    for x, y, w, h in bounding_boxes:
        sub_image = image[y : y + h, x : x + w]
        if contains_skin(sub_image, thresh=5):
            filtered_bounding_boxes.append((x, y, w, h))

    logger.info(f"Found {len(filtered_bounding_boxes)} images")

    return filtered_bounding_boxes

def match_size(images: list[np.ndarray]) -> list[np.ndarray]:
    """
    Resize images to the size of the largest
    image by adding black borders
    """
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
                ))
        else:
            resized_images.append(img)
    return resized_images

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
    scale = compute_resize_scale(img.shape,
                                 min_side=min_side,
                                 max_side=max_side)
    img = cv.resize(img, None, fx=scale, fy=scale)
    return img,  scale