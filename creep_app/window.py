import logging
import win32ui
import win32process as wproc
import ctypes
import cv2 as cv
import psutil
import numpy as np

logger = logging.getLogger(__name__)

user32 = ctypes.windll.user32

class Window:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        
        try:
            self.title = self.hwnd.GetWindowText()
        except:
            self.title = "Unknown Title"
        
        try:
            self.pid = wproc.GetWindowThreadProcessId(self.hwnd.GetSafeHwnd())[1]
            self.exec_name = psutil.Process(self.pid).name()
        except:
            logger.exception("Unable to get window pid / exec_name")
            self.pid = -1
            self.exec_name = "Unknown Executable"
        
        try:
            self.dpi = user32.GetDpiForWindow(self.hwnd.GetSafeHwnd())
        except:
            self.dpi = 96
        
    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title
    
    def get_coordinates(self):
        
        try:
            client_rect = self.hwnd.GetClientRect()
            logger.debug(f"Client rect: {client_rect}")
            
            window_rect = self.hwnd.GetWindowRect()
            logger.debug(f'Window rect: {window_rect}')
        except:
            logger.exception("Unable to get window coordinates")
            return None

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
    
    def image(self, sct):
        coordinates = self.get_coordinates()
        image = sct.grab(coordinates)
        image = np.array(image)[:, :, :3]

        # Scale image to 96 DPI
        if self.dpi != 96:
            scale = self.dpi / 96
            image = cv.resize(image, None, fx=scale, fy=scale)

        return image
    
    def is_stable(self):
        window_2 = Window.activeWindow()
        if window_2 is None or window_2.title != self.title:
            return False
        else:
            return True

    @classmethod
    def activeWindow(cls,invalid_title: str | None = None):
        try:
            hwnd = win32ui.GetForegroundWindow()
            window = cls(hwnd)
            if window.title == invalid_title:
                return None
            else:
                return window
        except:
            return None
    
    
    






