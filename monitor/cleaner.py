import requests
import time
import logging
from openchaver.decorators import handle_error
from openchaver.const import PORT
logger = logging.getLogger(__name__)

@handle_error
def run_cleaner():
    while True:
        try:
            response = requests.post(f"http://localhost:{PORT}/api/screenshots/clean/")
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            logger.error(e)
            logger.error(response.text)
        time.sleep(60)

