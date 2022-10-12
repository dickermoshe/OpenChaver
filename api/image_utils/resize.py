import numpy as np
import cv2 as cv


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
