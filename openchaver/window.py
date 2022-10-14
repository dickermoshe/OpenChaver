import logging
import os

import numpy as np
import cv2 as cv
import mss

from .utils import is_profane, deblot_image, contains_skin

# Logger
logger = logging.getLogger(__name__)


# Exceptions
class NoWindowFound(Exception):
    def __init__(self, title = None, message="No Active Window Found"):
        self.message = message
        self.current_title = title
        super().__init__(self.message)
    pass


class UnstableWindow(Exception):
    def __init__(self, title = None, message="Window is Unstable"):
        self.message = message
        self.current_title = title
        super().__init__(self.message)
    pass


class WindowDestroyed(Exception):
    """Window has been destroyed"""
    pass

class WindowBase:
    def __init__(self) -> None:
        self.nsfw_detections = None
        self.is_nsfw = False

    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title

    def take_screenshot(self):
        """Get a screenshot of the window"""

        # Get the coordinates of the window
        coordinates = self.get_coordinates()

        # Get the image
        with mss.mss() as sct:
            image = sct.grab(coordinates)
            image = np.array(image)[:, :, :3] # Remove alpha channel

        # Scale image to self.DEFAULT_DPI DPI
        if self.dpi != self.DEFAULT_DPI:
            logger.debug(f"Scaling image to {self.DEFAULT_DPI} DPI")
            scale = self.dpi / self.DEFAULT_DPI
            image = cv.resize(image, None, fx=scale, fy=scale)

        self.image = image
    
    def stable_check(self) -> None:
        """Check if the window is stable"""
        try:
            window_2 = self.__class__.get_active_window()
            if window_2.title != self.title:
                raise UnstableWindow(window_2.title)
        except UnstableWindow:
            raise
        except:
            raise UnstableWindow
    
    def run_detection(
        self,
        opennsfw=None,
        nudenet=None,
    ):
        from .nudenet import NudeNet
        from .opennsfw import OpenNsfw


        # Get the image
        image = self.image

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
        min_size = (0.0025 * mask.shape[0] * mask.shape[1])
        mask = deblot_image(mask, min_size=min_size)

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
                nudenet_results = nudenet.is_nsfw(i)
                if nudenet_results['is_nsfw']:
                    logger.debug("NSFW image detected")
                    self.is_nsfw = True
                    self.nsfw_detections = nudenet_results
                    return
                else:
                    logger.debug("NudeNet did not detect NSFW image")
    

        

if os.name == "nt":
    import ctypes
    import time

    import win32ui
    import win32process as wproc
    import psutil

    class Window(WindowBase):
        DEFAULT_DPI = 96
        user32 = ctypes.windll.user32
        def __init__(self, hwnd):
            super().__init__()

            self.hwnd = hwnd

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
            

        @classmethod
        def get_active_window(cls, invalid_title: str | None = None,stable: bool|int = False):
            """Get the active window"""
            try:
                # Get the active window
                hwnd = win32ui.GetForegroundWindow()
                window = cls(hwnd)

                # Check for an invalid title
                if window.title == invalid_title:
                    raise NoWindowFound(window.title)
                logger.debug(f"Active window: {window.title}")

                
                # Check if the window is stable
                for _ in range(int(stable)):
                    window.stable_check()
                    time.sleep(1)
                
                return window
            
            except UnstableWindow:
                raise
            except NoWindowFound:
                raise
            except:
                raise NoWindowFound

else:
    print("Unsupported OS")
    exit(1)

