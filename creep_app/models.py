import logging
import time
from mss.windows import MSS
import numpy as np
import cv2 as cv
from django.db import models
from django.utils.html import mark_safe
from google.oauth2.credentials import Credentials
from django.core.files.base import ContentFile
from django.conf import settings
from solo.models import SingletonModel
import requests
from google_auth_oauthlib.flow import InstalledAppFlow
import os
from googleapiclient.discovery import build
from google.auth.exceptions import RefreshError
from email.message import EmailMessage
import base64
from google.auth.transport.requests import Request
import random

from creep_app.window import Window

logger = logging.getLogger("django")


def get_callback_process(queue):
    import http.server

    class MyHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"OK")
            self.server.code = self.path
            self.server.stop = True

    server = http.server.HTTPServer(("localhost", 8080), MyHandler)
    server.stop = False
    while not server.stop:
        server.handle_request()
    queue.put(server.code)


class Config(SingletonModel):
    """Configuration for the app"""

    gmail_account = models.CharField(max_length=100, blank=True, null=True)
    access_token = models.CharField(max_length=100, blank=True, null=True)
    refresh_token = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return "Config"

    class Meta:
        verbose_name = "Config"

    @classmethod
    def add_account(cls):
        """Add a gmail account"""

        try:
            config = cls.objects.get()
            logger.info("Account already added. You must delete it first")
            return False
        except cls.DoesNotExist:
            config = cls()

        os.environ["OAUTHLIB_RELAX_TOKEN_SCOPE"] = "1"
        flow = InstalledAppFlow.from_client_config(
            {
                "installed": {
                    "client_id": settings.GOOGLE_CLIENT_ID,
                    "project_id": "openchaver",
                    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                    "token_uri": "https://oauth2.googleapis.com/token",
                    "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
                    "client_secret": settings.GOOGLE_CLIENT_SECRET,
                    "redirect_uris": ["http://localhost"],
                }
            },
            [
                "https://www.googleapis.com/auth/gmail.send",
                "https://www.googleapis.com/auth/userinfo.email",
            ],
        )
        creds = flow.run_local_server(port=0)
        config.gmail_account = creds.id_token["email"]
        config.access_token = creds.token
        config.refresh_token = creds.refresh_token
        config.save()
        return True

    @property
    def credentials(self):
        """Return credentials"""

        # Create credentials
        creds = Credentials.from_authorized_user_info(
            {
                "access_token": self.access_token,
                "refresh_token": self.refresh_token,
                "token_uri": "https://oauth2.googleapis.com/token",
                "client_id": settings.GOOGLE_CLIENT_ID,
                "client_secret": settings.GOOGLE_CLIENT_SECRET,
                "scopes": [
                    "https://www.googleapis.com/auth/gmail.send",
                    "https://www.googleapis.com/auth/userinfo.email",
                ],
            }
        )

        # Refresh token if needed
        if creds.expired:
            try:
                creds.refresh(Request())
            except RefreshError:
                logger.error("Error refreshing token")
                return None
            self.access_token = creds.token
            self.save()

        return creds

    @classmethod
    def send_email(cls, subject, body:str):
        """Send an email"""
        config = cls.objects.get()
        creds = config.credentials
        service = build('gmail', 'v1', credentials=creds)

        message = EmailMessage()

        message["to"] = config.gmail_account
        message["from"] = config.gmail_account
        message["subject"] = subject

        message.set_content(body)

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

        create_message = {
            'raw': encoded_message
        }
        service.users().messages().send(userId="me", body=create_message).execute()

    @classmethod
    def remove_account(cls):
        """Remove the gmail account"""

        try:
            config = cls.objects.get()
        except cls.DoesNotExist:
            logger.info("No account to remove")
        
        cls.send_email("Goodbye","Goodbye World")
        config.delete()




class Screenshot(models.Model):
    """This is the model for a screenshot"""

    #: The image file
    image = models.ImageField(upload_to="images/")

    #: Whether or not the image is NSFW
    is_nsfw = models.BooleanField(default=None, null=True, blank=True)

    #: The title of the window that the screenshot was taken from
    title = models.CharField(
        max_length=200,
    )

    #: The executable name of the window that the screenshot was taken from
    exec_name = models.CharField(
        max_length=200,
    )

    #: Alerted
    alerted = models.BooleanField(default=False)

    #: Whether or not to keep the image for 7 days
    keep = models.BooleanField(default=False)

    #: The date and time the screenshot was created
    created = models.DateTimeField(auto_now_add=True)

    #: The date and time the screenshot was last updated
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.image.name

    def image_tag(self):
        """Returns an image tag for the image for the admin page"""
        return mark_safe('<img src="/media/%s" width="300" />' % (self.image))

    class Meta:
        ordering = ["-created"]

    def cv_image(self):
        """
        Returns the image as a cv2 image.
        If the image file does not exist, the record is deleted. Returns None if the image file does not exist.
        :return: The image as a cv2 image or None if the image file does not exist
        """

        try:
            return cv.imread(self.image.path)
        except:
            self.delete()
            return None

    @classmethod
    def grab_screenshot(
        cls,
        sct: MSS,
        max_tries: int,
        invalid_title: str | None = None,
        stable_window: bool | int = True,
    ):
        """
        Grabs a screenshot from the active window
        :param sct: The MSS client
        :param max_tries: The maximum amount of times to try to grab a screenshot before not waiting any longer
        :return: The screenshot as a cv2 image, the window title, and the window executable name
        """
        # If max_tries is at 0 then return whatever is in the active window
        if max_tries == 0:
            window = Window.activeWindow()
            if window is None:
                logger.warning("Window not found")
                return None, None, None
            else:
                logger.info("Found window: %s", window.title)
                return window.image(sct), window.title, window.exec_name

        # Otherwise, Respect the stable_window and invalid_title parameters
        else:
            window = Window.activeWindow(invalid_title=invalid_title)
            if window is None:
                time.sleep(0.5)
                return cls.grab_screenshot(
                    sct, max_tries - 1, invalid_title, stable_window
                )

            if stable_window != False:
                for _ in range(int(stable_window) * 2):
                    if window.is_stable() == False:
                        time.sleep(0.5)
                        return cls.grab_screenshot(
                            sct, max_tries - 1, invalid_title, stable_window
                        )
                    time.sleep(0.5)

            logger.info("Found window: %s", window.title)
            return window.image(sct), window.title, window.exec_name

    @classmethod
    def save_screenshot(
        cls,
        img: np.ndarray,
        title: str,
        exec_name: str,
        keep: bool = False,
        is_nsfw: bool | None = None,
        bounding_boxes: list = [],
    ):
        """
        Save an image to the database

        :param img: The image to save
        :param title: The title of the window that the screenshot was taken from
        :param exec_name: The executable name of the window that the screenshot was taken from
        :return: The screenshot object or None if the image could not be saved
        """

        # Create a screenshot object
        try:
            screenshot = cls()
            _, buffer = cv.imencode(".png", img)
            screenshot.image.save(f"{int(time.time())}.png", ContentFile(buffer))
            screenshot.title = title
            screenshot.exec_name = exec_name
            screenshot.keep = keep
            screenshot.is_nsfw = is_nsfw
            screenshot.bounding_boxes = bounding_boxes
            screenshot.save()
            return screenshot
        except:
            logger.exception("Could not save screenshot")
            return None


class Alert(models.Model):
    """This is the model for an alert"""

    #: The screenshot that triggered the alert
    screenshots = models.ManyToManyField(Screenshot, related_name="alerts")

    # Whether or not the alert has been sent
    sent = models.BooleanField(default=False)

    #: The date and time the alert was created
    created = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Alert {self.id}"

    class Meta:
        ordering = ["-created"]

    def send(self):
        """Send the alert"""
        print("Sending alert")
        self.sent = True
        self.save()

    @classmethod
    def send_alerts(cls):
        pass
