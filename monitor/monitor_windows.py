import time
import requests
from uuid import uuid4
import logging
from openchaver.decorators import handle_error
from .afk import seconds_since_last_input
from .window import Window, UnstableWindow, NoWindowFound
from openchaver.const import PORT
logger = logging.getLogger(__name__)


class WindowMonitor:
    def __init__(
        self,
        sleep_interval=1,
        meta_interval=1,
        image_interval=300,
        nsfw_interval=10,
        stable=5,
        away=60,
    ) -> None:
        self.sleep_interval = sleep_interval
        self.meta_interval = meta_interval
        self.image_interval = image_interval
        self.nsfw_interval = nsfw_interval
        self.stable = stable
        self.away = away
        self.window = Window.get_active_window()
        self.meta_timer = time.time()
        self.image_timer = time.time()
        self.nsfw_timer = time.time()

    @handle_error
    def upload_screenshot(self, window: Window, screenshot_type="META"):
        """Upload the screenshot to the server"""
        png_bytes = window.take_screenshot() if screenshot_type in ["IMAGE", "NSFW", "NSFW_IMAGE", "NSFW_META"] else None
        data = {
            "title": window.title,
            "excutable_name": window.exec_name,
            "screenshot_type": screenshot_type,
        }
        # Set the image name to the window title
        files = {"image_file": (f'{uuid4}.png', png_bytes, "image/png")} if png_bytes else None

        response = requests.post(
            f"http://localhost:{PORT}/api/screenshots/", data=data, files=files)
        try:
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(e)
            logger.error(response.text)



    def screenshoot(
        self,
    ) -> None:
        """Take a screenshot of the window"""
        meta = False
        image = False
        nsfw = False

        # Get the active window
        try:
            window = Window.get_active_window(
                invalid_title=self.window.title, stable=self.stable
            )
            # If meta interval has passed
            if time.time() - self.meta_timer > self.meta_interval:
                meta = True
                self.meta_timer = time.time()

            # If image interval has passed
            if time.time() - self.image_timer > self.image_interval:
                image = True
                self.image_timer = time.time()

            # If nsfw interval has passed
            if time.time() - self.nsfw_timer > self.nsfw_interval:
                nsfw = True
                self.nsfw_timer = time.time()

            if image and nsfw:  # Keep image - scan nsfw
                self.upload_screenshot(window, screenshot_type="NSFW_IMAGE")

            elif meta and image:  # Keep image - dont scan nsfw
                self.upload_screenshot(window, screenshot_type="IMAGE")

            elif meta and nsfw:  # Dont keep image - scan nsfw
                self.upload_screenshot(window, screenshot_type="NSFW_META")

            elif meta:  # Dont keep image - dont scan nsfw
                self.upload_screenshot(window, screenshot_type="META")

            elif image:  # Keep image - dont scan nsfw
                self.upload_screenshot(window, screenshot_type="IMAGE")

            elif nsfw:  # Dont keep image - scan nsfw
                self.upload_screenshot(window, screenshot_type="NSFW")

        except (UnstableWindow, NoWindowFound):
            pass
        except:
            logger.exception("Error in Screenshooter")

    def is_afk(self) -> bool:
        """Check if the user is afk"""
        return seconds_since_last_input() > self.away

    @handle_error
    def run(
        self,
    ):
        """
        Run the monitor
        """

        while True:
            time.sleep(self.sleep_interval / 2)

            # Screenshoot if not afk
            if not self.is_afk():
                self.screenshoot()

            time.sleep(self.sleep_interval / 2)

def run_monitor():
    """Run the monitor"""
    monitor = WindowMonitor()
    monitor.run()
