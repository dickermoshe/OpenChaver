import logging
import time

import win32ui
import win32process as wproc
import psutil

logger = logging.getLogger(__name__)

class Window:
    def __init__(self, hwnd):
        self.hwnd = hwnd
        
        try:
            logger.debug("Getting window title")
            self.title = self.hwnd.GetWindowText()
        except:
            logger.exception("Unable to get window title")
            self.title = "Unknown Title"
        
        try:
            logger.debug("Getting window PID")
            self.pid = wproc.GetWindowThreadProcessId(self.hwnd.GetSafeHwnd())[1]
            logger.debug("Getting process name")
            self.exec_name = psutil.Process(self.pid).name()
        except:
            logger.exception("Unable to get window pid / exec_name")
            self.pid = -1
            self.exec_name = "Unknown Executable"
        
    def __str__(self):
        return self.title

    def __repr__(self):
        return self.title
    
    def get_coordinates(self):
        
        try:
            logger.debug("Getting raw client coordinates...")
            client_rect = self.hwnd.GetClientRect()
            logger.debug(f"Client rect: {client_rect}")
            
            logger.debug("Getting raw window coordinates...")
            window_rect = self.hwnd.GetWindowRect()
            logger.debug(f'Window rect: {window_rect}')
        except:
            logger.exception("Unable to get window coordinates")
            return None

        logger.debug("Calculating coordinates...")
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
    
    @classmethod
    def activeWindow(cls):
        try:
            logger.debug("Getting active window...")
            hwnd = win32ui.GetForegroundWindow()
            return cls(hwnd)
        except:
            logger.exception("Unable to get active window")
            return None
    
    @classmethod
    def waitForActiveWindow(cls, max_wait: int = 60,invalid_title : str | None = None ):
        logger.debug(f"Waiting for active window for {max_wait} seconds")
        logger.debug(f"Invalid title: {invalid_title}") if invalid_title != None else None
        
        time_waited = 0
        while time_waited < max_wait:
            window = cls.activeWindow()
            if window != None and window.title != invalid_title:
                return window , max_wait - time_waited
            time.sleep(1)
            time_waited += 1
        
        time_remaining = max_wait - time_waited
        return None , time_remaining





