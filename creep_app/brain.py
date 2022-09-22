import logging

import cv2 as cv
import numpy as np
from PIL import Image

from django.conf import settings

logger = logging.getLogger(__name__)

def read_image_bgr(image):
    """ Read an image in BGR format.
    Args
        path: Path to the image.
    """
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

    img = cv.resize(img, None, fx=scale, fy=scale)

    return img, scale

def preprocess_image(
    image_path, min_side, max_side,
):
    image = read_image_bgr(image_path)
    image = _preprocess_image(image)
    image, scale = resize_image(image, min_side=min_side, max_side=max_side)
    return image, scale


class Brain:
    def __init__(self):
        logger.debug("Initializing Detector")
        model_path = settings.BASE_DIR  / 'nsfw_model' / 'detector_v2_default_checkpoint.onnx'

        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found: {model_path}")
        
        import onnxruntime
        self.detection_model = onnxruntime.InferenceSession(str(model_path),providers=['CPUExecutionProvider'])
        self.classes = ['EXPOSED_ANUS', 'EXPOSED_ARMPITS', 'COVERED_BELLY', 'EXPOSED_BELLY', 'COVERED_BUTTOCKS', 'EXPOSED_BUTTOCKS', 'FACE_F', 'FACE_M', 'COVERED_FEET',
                        'EXPOSED_FEET', 'COVERED_BREAST_F', 'EXPOSED_BREAST_F', 'COVERED_GENITALIA_F', 'EXPOSED_GENITALIA_F', 'EXPOSED_BREAST_M', 'EXPOSED_GENITALIA_M']

    def detect(self, images: list[np.ndarray], min_prob=None, fast=False, batch_size=5) -> list[dict]:
        """ Detect objects in an image."""
        
        # Preprocess images
        preprocessed_images = [
            preprocess_image(
                img,
                min_side=480 if fast else 800,
                max_side=800 if fast else 1333
                ) for img in images
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

            for frame_boxes, frame_scores, frame_labels, in zip(
                    boxes, scores, labels,
                ):
                frame_result = {
                    "detections":[],
                }
                for box, score, label in zip(
                        frame_boxes, frame_scores, frame_labels
                    ):
                    if score < min_prob:
                        continue
                    box = box.astype(int).tolist()
                    label = self.classes[label]
                    detection = {"box": [int(c) for c in box], "score": float(score), "label": label}
                    frame_result['detections'].append(detection)
                
                frame_result['is_nsfw'] = self._eval_detection(frame_result['detections'])
                results.append(frame_result)

        return results
    
    
    def splice(self,img:np.ndarray) -> list[np.ndarray]:

        colored_pixels = self.colorful(img)
        _,thresholded_colored_pixels = cv.threshold(colored_pixels,0,255,cv.THRESH_BINARY+cv.THRESH_OTSU)

        mser_pixels = self.mser(img,'color')

        mask = cv.bitwise_or(thresholded_colored_pixels,mser_pixels)

        # Dialation and erosion
        kernel = np.ones((3,3),np.uint8)
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE  , kernel,iterations=5)
        mask = cv.morphologyEx(mask, cv.MORPH_OPEN  , kernel,iterations=5)
        mask = self.deblot(mask,min_size=500)

        masked_img = cv.bitwise_and(img,img,mask=mask)

        bounding_boxes = self.get_bounding_boxes(masked_img)
        filtered_bounding_boxes = self.filter_bounding_boxes(bounding_boxes)

        images = []

        # Cut out the bounding boxes
        for x,y,w,h in filtered_bounding_boxes:
            images.append(img[y:y+h,x:x+w])

        return images
     
    def _eval_detection(self, result, threshold=0.5):
        nsfw_labels = ['EXPOSED_ANUS', 'EXPOSED_BUTTOCKS','EXPOSED_BREAST_F', 'EXPOSED_GENITALIA_F','EXPOSED_GENITALIA_M']
        for detection in result:
            if detection['label'] in nsfw_labels and detection['score'] > threshold:
                return True
        return False

    def deblot(self,img,min_size=10000):
        # find all of the connected components (white blobs in your image).
        # im_with_separated_blobs is an image where each detected blob has a different pixel value ranging from 1 to nb_blobs - 1.
        nb_blobs, im_with_separated_blobs, stats, _ = cv.connectedComponentsWithStats(img)
        # stats (and the silenced output centroids) gives some information about the blobs. See the docs for more information. 
        # here, we're interested only in the size of the blobs, contained in the last column of stats.
        sizes = stats[:, -1]
        # the following lines result in taking out the background which is also considered a component, which I find for most applications to not be the expected output.
        # you may also keep the results as they are by commenting out the following lines. You'll have to update the ranges in the for loop below. 
        sizes = sizes[1:]
        nb_blobs -= 1

        # output image with only the kept components
        im_result = np.zeros((img.shape))

        # for every component in the image, keep it only if it's above min_size
        for blob in range(nb_blobs):
            if sizes[blob] >= min_size:
                # see description of im_with_separated_blobs above
                im_result[im_with_separated_blobs == blob + 1] = 255
        
        # Convert to 8 bit image
        im_result = im_result.astype(np.uint8)

        return im_result

    def boring_area(self,img,shift=1):

        # Compare every pixel with its neighbors
        if len(img.shape) == 3:
            gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
        else:
            gray = img
        
        # Shift the image to the right
        shift_r = np.roll(gray,shift,axis=1)
        # Shift the image to the left
        shift_l = np.roll(gray,shift * -1,axis=1)
        # Shift the image up
        shift_u = np.roll(gray,shift,axis=0)
        # Shift the image down
        shift_d = np.roll(gray,shift * -1,axis=0)

        # Compare every pixel with its neighbors
        diff_r = np.absolute(gray - shift_r)
        diff_l = np.absolute(gray - shift_l)
        diff_u = np.absolute(gray - shift_u)
        diff_d = np.absolute(gray - shift_d)
        
        # Multiply the differences
        diff = diff_r * diff_l * diff_u * diff_d
        
        return diff

    def mser(self,img,fields = 'color',):
        images =[]
        if fields == 'color':
            images.append(img)
        if fields == 'gray' or fields == 'all':
            images.append(cv.cvtColor(img, cv.COLOR_BGR2GRAY))
        if fields == 'red' or fields == 'all':
            images.append(img[:,:,2])
        if fields == 'green' or fields == 'all':
            images.append(img[:,:,1])
        if fields == 'blue' or fields == 'all':
            images.append(img[:,:,0])
        
        images = [self._single_mser(img) for img in images]
        matte = images[0]
        for i in range(len(images)-1):
            matte = cv.bitwise_or(matte,images[i+1])
        
        return matte

    def colorful(self,img):
        # Remove parts of the image that are not colored

        red, green, blue = cv.split(img)
        
        r_g = np.absolute(red - green)
        r_b = np.absolute(red - blue)
        g_b = np.absolute(green - blue)

        diff = r_g + r_b + g_b

        return diff
  
    def get_bounding_boxes(self,img,min_area = 10000,aspect_ratio = 3,):
        if len(img.shape) == 3:
            gray = cv.cvtColor(img,cv.COLOR_BGR2GRAY)
        else:
            gray = img
        contours, _ = cv.findContours(gray, cv.RETR_TREE, cv.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv.contourArea(c) > min_area]

        bounding_boxes = []

        for cnt in contours:
            x,y,w,h = cv.boundingRect(cnt)
        

            # If the images aspect ratio is very narrow or very wide, skip it
            if w / h > aspect_ratio or w / h < aspect_ratio * .1:
                continue

            bounding_boxes.append((x,y,w,h))
        
        return bounding_boxes
    
    def _single_mser(self,img):

        mser = cv.MSER_create()
        regions , _ = mser.detectRegions(img)
        hulls = [cv.convexHull(p.reshape(-1, 1, 2)) for p in regions]
        mask = np.zeros((img.shape[0], img.shape[1], 1), dtype=np.uint8)
        for contour in hulls:
            if len(contour) > 2:
                # If contour is too small, ignore it
                if cv.contourArea(contour) < 1500:
                    cv.drawContours(mask, [contour], -1, (255, 255, 255),-1)
        return mask
   
    def filter_bounding_boxes(self,bounding_boxes):
        """Remove bounding boxes that are contained in other bounding boxes"""
        filtered_boxes = []
        for box in bounding_boxes:
            x,y,w,h = box
            contained = False
            for box2 in bounding_boxes:
                x2,y2,w2,h2 = box2
                if x2 < x and y2 < y and x2 + w2 > x + w and y2 + h2 > y + h:
                    contained = True
                    break
            if not contained:
                filtered_boxes.append(box)
        return filtered_boxes
    
    def skin_pixels(self,img:np.ndarray|list[np.ndarray],threshold = 100):

        if type(img) == list:
            if len(img) == 0:
                return False
            if len(img) == 1:
                img = img[0]
            else:
                img = self.match_size(img)
                img = np.concatenate(img,axis=1)

        # Convert image to HSV
        img_copy = img.copy()
        blured = cv.GaussianBlur(img_copy, (5, 5), 0)

        min_HSV = np.array([0, 58, 30], dtype="uint8")
        max_HSV = np.array([33, 255, 255], dtype="uint8")

        imageHSV = cv.cvtColor(blured, cv.COLOR_BGR2HSV)
        skinRegionHSV = cv.inRange(imageHSV, min_HSV, max_HSV)

        return np.count_nonzero(skinRegionHSV) > threshold
    
    def match_size(self,images:list[np.ndarray])->list[np.ndarray]:
        """Resize images to the size of the largest image by adding black borders"""
        max_width = max([img.shape[1] for img in images])
        max_height = max([img.shape[0] for img in images])
        resized_images = []
        for img in images:
            if img.shape[1] < max_width or img.shape[0] < max_height:
                resized_images.append(cv.copyMakeBorder(img,0,max_height - img.shape[0],0,max_width - img.shape[1],cv.BORDER_CONSTANT,value=[0,0,0]))
            else:
                resized_images.append(img)
        return resized_images
