# No proxy for local server
import os
os.environ['NO_PROXY'] = 'localhost'

from .const import *  # noqa
from .logger import *  # noqa
