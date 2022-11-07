import logging
import os
import psutil
import time
import numpy as np
import cv2 as cv
import mss
from io import BytesIO

from core.image_utils import encode_numpy_to_base64, numpy_to_png_bytes

# Logger
logger = logging.getLogger(__name__)


# Exceptions
class NoWindowFound(Exception):
    def __init__(self, title=None, message="No Active Window Found"):
        self.message = message
        self.current_title = title
        super().__init__(self.message)

    pass


class UnstableWindow(Exception):
    def __init__(self, title=None, message="Window is Unstable"):
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

    def take_screenshot(self) -> bytes:
        """Get a screenshot of the window"""

        # Get the coordinates of the window
        coordinates = self.get_coordinates()

        # Get the image
        with mss.mss() as sct:
            image = sct.grab(coordinates)
            image = np.array(image)[:, :, :3]  # Remove alpha channel

        # Scale image to self.DEFAULT_DPI DPI
        if self.dpi != self.DEFAULT_DPI:
            logger.info(f"Scaling image to {self.DEFAULT_DPI} DPI")
            scale = self.dpi / self.DEFAULT_DPI
            image = cv.resize(image, None, fx=scale, fy=scale)

        png_bytes = numpy_to_png_bytes(image)
        
        # Return a bufffed reader for a post requests file upload
        return png_bytes

        




    def stable_check(self) -> None:
        """Check if the window is stable"""
        try:
            window_2 = self.__class__.get_active_window(recursive=True)
            if window_2.title != self.title:
                raise UnstableWindow(window_2.title)
        except UnstableWindow:
            raise
        except:  # noqa: E722
            raise UnstableWindow


if os.name == "nt":
    import ctypes
    import win32ui
    import win32process as wproc
    

    class Window(WindowBase):
        DEFAULT_DPI = 96
        user32 = ctypes.windll.user32

        def __init__(self, hwnd):
            super().__init__()

            self.hwnd = hwnd
            self.title = "Unknown Title"
            self.exec_name = "Unknown Executable"
            self.pid = -1

            # Get the window title
            try:
                self.title = self.hwnd.GetWindowText()
            except:  # noqa: E722
                logger.exception("Unable to get window title")

            # Get the window process ID and executable path
            try:
                self.pid = wproc.GetWindowThreadProcessId(self.hwnd.GetSafeHwnd())[1]
                self.exec_name = psutil.Process(self.pid).name()
            except:  # noqa: E722
                logger.exception("Unable to get window pid | exec_name")

            # Get the window DPI
            try:
                self.dpi = self.user32.GetDpiForWindow(self.hwnd.GetSafeHwnd())
            except:  # noqa: E722
                logger.exception(
                    f"Unable to get window DPI - defaulting to {self.DEFAULT_DPI}"  # noqa: E501
                )
                self.dpi = self.DEFAULT_DPI

        def get_coordinates(self):
            """Get the coordinates of the window"""

            # The following code is used to calculate the coordinates of
            # the window with the border monitor pixels removed
            try:
                client_rect = self.hwnd.GetClientRect()
                logger.info(f"Client rect: {client_rect}")

                window_rect = self.hwnd.GetWindowRect()
                logger.info(f"Window rect: {window_rect}")
                client_width = client_rect[2] - client_rect[0]
                window_width = window_rect[2] - window_rect[0]
                border = (window_width - client_width) // 2

                coordinates = (
                    window_rect[0] + border,
                    window_rect[1] + border,
                    window_rect[2] - border,
                    window_rect[3] - border,
                )
                logger.info(f"Calculated coordinates: {coordinates}")

                return coordinates
            except:  # noqa: E722
                logger.exception("Unable to get window coordinates")
                raise WindowDestroyed

        @classmethod
        def get_active_window(
            cls,
            invalid_title: str | None = None,
            stable: bool | int = False,
            recursive: bool = False,
        ):
            """Get the active window"""
            try:
                # Get the active window
                hwnd = win32ui.GetForegroundWindow()
                window = cls(hwnd)

                # Check for an invalid title
                if window.title == invalid_title:
                    raise NoWindowFound(window.title)

                if not recursive:
                    logger.info(f"Active window: {window.title}")

                # Check if the window is stable
                for _ in range(int(stable)):
                    window.stable_check()
                    time.sleep(1)

                return window

            except UnstableWindow:
                raise
            except NoWindowFound:
                raise 
            except:  # noqa: E722
                raise NoWindowFound

else:
    print("Unsupported OS")
    exit(1)
