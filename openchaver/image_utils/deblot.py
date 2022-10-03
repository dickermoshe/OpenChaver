import numpy as np
import cv2 as cv

def deblot(mask:np.ndarray,min_size:float):
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