import time
import requests
import logging
import subprocess
from openchaver.decorators import handle_error
from .afk import seconds_since_last_input
from .window import Window, UnstableWindow, NoWindowFound
from openchaver.const import PORT, TESTING, MIGRATE_COMMAND

from django.contrib.auth.models import User

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
        data = {
            "title": window.title,
            "executable_name": window.exec_name,
            "base64_image": window.take_screenshot()
            if screenshot_type in ["IMAGE", "NSFW", "NSFW_IMAGE", "NSFW_META"]
            else None,
            "screenshot_type": screenshot_type,
        }
        response = requests.post(
            f"http://localhost:{PORT}/api/screenshots/", json=data
        )
        response.raise_for_status()

    def screenshoot(self) -> None:
        """Take a screenshot of the window"""
        meta = False
        image = False
        nsfw = False

        try:
            window = Window.get_active_window(
                invalid_title=self.window.title, stable=self.stable
            )

            if time.time() - self.meta_timer > self.meta_interval:
                meta = True
                self.meta_timer = time.time()

            if time.time() - self.image_timer > self.image_interval:
                image = True
                self.image_timer = time.time()

            if time.time() - self.nsfw_timer > self.nsfw_interval:
                nsfw = True
                self.nsfw_timer = time.time()

            if image and nsfw:
                self.upload_screenshot(window, screenshot_type="NSFW_IMAGE")
            elif meta and image:
                self.upload_screenshot(window, screenshot_type="IMAGE")
            elif meta and nsfw:
                self.upload_screenshot(window, screenshot_type="NSFW_META")
            elif meta:
                self.upload_screenshot(window, screenshot_type="META")
            elif image:
                self.upload_screenshot(window, screenshot_type="IMAGE")
            elif nsfw:
                self.upload_screenshot(window, screenshot_type="NSFW")

        except (UnstableWindow, NoWindowFound):
            pass
        except:
            logger.exception("Error in Screenshooter")

    def is_afk(self) -> bool:
        return seconds_since_last_input() > self.away

    @handle_error
    def run(self):
        while True:
            time.sleep(self.sleep_interval / 2)
            if not self.is_afk():
                self.screenshoot()
            time.sleep(self.sleep_interval / 2)


def run_monitor():
    """Run the monitor"""

    # Run migrations and create admin if in TESTING mode
    subprocess.run(MIGRATE_COMMAND)
    if TESTING:
        try:
            if not User.objects.filter(username='admin').exists():
                User.objects.create_superuser('admin', 'admin@example.com', 'pass')
        except Exception as e:
            logger.exception(e)

    monitor = WindowMonitor()
    monitor.run()
