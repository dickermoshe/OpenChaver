# Imports
import logging
import ctypes
import time
from pathlib import Path

import win32ui
import win32process as wproc
import cv2 as cv
import psutil
import numpy as np
import mss
import dataset

try:
    from . import image_database_path , image_database_url
    from .image_utils.skin_detector import contains_skin
    from .image_utils.obfuscate import blur, pixelate
    from .profanity import is_profane
except ImportError:
    from openchaver import image_database_path , image_database_url
    from image_utils.skin_detector import contains_skin
    from image_utils.obfuscate import blur, pixelate
    from profanity import is_profane

# Logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)




# Exceptions
class NoWindowFound(Exception):
    """No Active Window Found"""

    pass


class InvalidWindow(Exception):
    """Window found is not valid"""

    pass


class UnstableWindow(Exception):
    """Window is not stable"""

    pass


class WindowDestroyed(Exception):
    """Window has been destroyed"""

    pass


# Windows OS Window class
class WinWindow:
    DEFAULT_DPI = 96
    user32 = ctypes.windll.user32

    def __init__(self, hwnd):
        self.hwnd = hwnd
        self.nsfw = False

        # Get the window title and check for profanity
        try:
            self.title = self.hwnd.GetWindowText()
            self.profane = is_profane(self.title)
        except:
            logger.exception("Unable to get window title")
            self.title = "Unknown Title"
            self.profane = False

        # Get the window process ID and executable path
        try:
            self.pid = wproc.GetWindowThreadProcessId(
                self.hwnd.GetSafeHwnd())[1]
            self.exec_name = psutil.Process(self.pid).name()
        except:
            logger.exception("Unable to get window pid | exec_name")
            self.pid = -1
            self.exec_name = "Unknown Executable"

        # Get the window DPI
        try:
            self.dpi = self.user32.GetDpiForWindow(self.hwnd.GetSafeHwnd())
        except:
            logger.exception(
                f"Unable to get window DPI - defaulting to {self.DEFAULT_DPI}")
            self.dpi = self.DEFAULT_DPI

        logger.debug(f"Window Title: {self.title}")
        logger.debug(f"Window Profane: {self.profane}")
        logger.debug(f"Window PID: {self.pid}")
        logger.debug(f"Window Executable: {self.exec_name}")
        logger.debug(f"Window DPI: {self.dpi}")

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    def __getstate__(self):  # This allows the object to be pickled
        state = self.__dict__.copy()
        del state["hwnd"]
        return state

    def __setstate__(self, state):  # This allows the object to be pickled
        self.__dict__.update(state)
        self.hwnd = None

    def get_coordinates(self):
        """Get the coordinates of the window"""

        # The following code is used to calculate the coordinates of
        # the window with the border monitor pixels removed
        try:
            client_rect = self.hwnd.GetClientRect()
            logger.debug(f"Client rect: {client_rect}")

            window_rect = self.hwnd.GetWindowRect()
            logger.debug(f"Window rect: {window_rect}")
            client_width = client_rect[2] - client_rect[0]
            window_width = window_rect[2] - window_rect[0]
            border = (window_width - client_width) // 2

            coordinates = (
                window_rect[0] + border,
                window_rect[1] + border,
                window_rect[2] - border,
                window_rect[3] - border,
            )
            logger.debug(f"Calculated coordinates: {coordinates}")

            return coordinates
        except:
            logger.exception("Unable to get window coordinates")
            raise WindowDestroyed
    def obfuscate_image(self):
        """
        Return pixelated image

        """
        self.image = pixelate(self.image)
        
    def take(self):
        """Get a screenshot of the window"""

        # Get the coordinates of the window
        coordinates = self.get_coordinates()

        # Get the image
        with mss.mss() as sct:
            logger.debug("Taking screenshot...")
            image = sct.grab(coordinates)
            image = np.array(image)[:, :, :3]

        # Scale image to self.DEFAULT_DPI DPI
        if self.dpi != self.DEFAULT_DPI:
            logger.debug(f"Scaling image to {self.DEFAULT_DPI} DPI")
            scale = self.dpi / self.DEFAULT_DPI
            image = cv.resize(image, None, fx=scale, fy=scale)

        self.image = image

    def check_stable(self):
        """Check if the window is stable"""
        try:
            window_2 = WinWindow.activeWindow()
            if window_2.title != self.title:
                raise UnstableWindow
        except:
            raise UnstableWindow

    @classmethod
    def activeWindow(cls, invalid_title: str | None = None):
        """Get the active window"""
        try:
            hwnd = win32ui.GetForegroundWindow()
            window = cls(hwnd)
            if window.title == invalid_title:
                raise InvalidWindow
            else:
                return window
        except:
            raise NoWindowFound

    @classmethod
    def grab_screenshot(
        cls,
        stable: float | bool = False,
        invalid_title: str | None = None,
    ):
        """
        Grabs a screenshot from the active window
        :param stable: Whether to wait for the window to be stable
        :param invalid_title: The title of the window to ignore
        """
        logger.debug("Grabbing screenshot...")
        logger.debug(f"Stable: {stable}")
        logger.debug(f"Invalid title: {invalid_title}")

        logger.debug("Getting active window")
        window = cls.activeWindow(invalid_title)

        if stable is False:
            # Take screenshot instantly
            logger.debug("Taking screenshot")
            window.take()
            return window
        else:
            # Wait for the window to be stable
            wait = float(stable)
            waited = 0
            while waited < wait:
                window.check_stable()
                time.sleep(0.5)
                waited += 0.5

            # Take screenshot
            logger.debug("Taking screenshot")
            window.take()
            return window

    def save_to_database(self):
        """Save the image to database"""
        try:
            db = dataset.connect(image_database_url)
        except:
            # Delete the database file and try again
            image_database_path.unlink()
            db = dataset.connect(image_database_url)
        
        try:
            table = db["images"]
            self.obfuscate_image()

            table.insert(dict(
                title=self.title,
                profane=self.profane,
                nsfw = self.nsfw,
                image=self.image,
                exec_name=self.exec_name,
                image=self.image,
                timestamp = time.time()
            ))
        except:
            logger.exception("Unable to save image to database")
            pass

        


    def run_detection(
        self,
        image: np.ndarray = None,
        opennsfw=None,
        nudenet=None,
    ):
        try:
            from .nsfw import NudeNet, OpenNsfw
        except ImportError:
            from nsfw import NudeNet, OpenNsfw
        # This function contains the complex logic of the application

        # Get the image
        image = image if image is not None else self.image

        # Check if there are skin pixels in the image
        # This is done to remove images that are definitely not NSFW
        if not contains_skin(image, thresh=0.5):
            logger.debug("Image does not contain skin. Skipping...")
            return


        # Remove all parts of the image that are very similar to their neighbors
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
        kernel = cv.getStructuringElement(cv.MORPH_ELLIPSE,
                                          (kernel_size, kernel_size))

        # Morphological operations on the mask
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

        # Deblot the mask
        nb_blobs, im_with_separated_blobs, stats, _ = cv.connectedComponentsWithStats(
            mask)
        sizes = stats[:, -1]
        sizes = sizes[1:]
        nb_blobs -= 1
        im_result = np.zeros((mask.shape))
        min_size = (0.0025 * mask.shape[0] * mask.shape[1]
                    )  # Set a relative minimum size for the blobs
        for blob in range(nb_blobs):
            if sizes[blob] >= min_size:
                im_result[im_with_separated_blobs == blob + 1] = 255
        mask = im_result.astype(np.uint8)

        # Morphological operations on the mask
        mask = cv.morphologyEx(mask, cv.MORPH_CLOSE, kernel, iterations=1)

        # Apply the mask to the image
        masked_image = cv.bitwise_and(image, image, mask=mask)

        # Detect individual images
        max_aspect_ratio = 3
        gray = cv.cvtColor(masked_image, cv.COLOR_BGR2GRAY)
        contours, _ = cv.findContours(gray, cv.RETR_TREE,
                                      cv.CHAIN_APPROX_SIMPLE)
        contours = [c for c in contours if cv.contourArea(c) > min_size]
        bounding_boxes = []
        for cnt in contours:
            x, y, w, h = cv.boundingRect(cnt)
            # If the images aspect ratio is very narrow or very wide, skip it
            if w / h > max_aspect_ratio or w / h < max_aspect_ratio * 0.1:
                continue
            bounding_boxes.append((x, y, w, h))
        images = []
        for x, y, w, h in bounding_boxes:
            images.append(image[y:y + h, x:x + w])

        # Remove images that dont contain skin
        images = list(filter(lambda i: contains_skin(i, thresh=5), images))


        # Run OpenNSFW on the images
        opennsfw = opennsfw if opennsfw is not None else OpenNsfw()
        for i in images:
            if opennsfw.is_nsfw(i):
                logger.debug("OpenNSFW detected NSFW image")
                # Run NudeNet on the images
                nudenet = nudenet if nudenet is not None else NudeNet()
                if nudenet.is_nsfw(i):
                    logger.debug("NudeNet detected NSFW image")
                    self.nsfw = True
                    logger.debug("NSFW image detected")
                    return
                else:
                    logger.debug("NudeNet did not detect NSFW image")
