from .__init__ import PROGRAM_NAME

import os
from pathlib import Path
from typing import Optional
import appdirs
from .utils import is_frozen


def get_data_dir(module_name: Optional[str] = None) -> Path:
    data_dir = appdirs.user_data_dir("openchaver")
    path = os.path.join(data_dir, module_name) if module_name else data_dir

    if not os.path.exists(path):
        os.makedirs(path)

    return Path(path)


def get_cache_dir(module_name: Optional[str] = None) -> Path:
    cache_dir = appdirs.user_cache_dir("openchaver")
    path = os.path.join(cache_dir, module_name) if module_name else cache_dir

    if not os.path.exists(path):
        os.makedirs(path)

    return Path(path)


def get_config_dir(module_name: Optional[str] = None) -> Path:
    config_dir = appdirs.user_config_dir("openchaver")
    path = os.path.join(config_dir, module_name) if module_name else config_dir

    if not os.path.exists(path):
        os.makedirs(path)

    return Path(path)


def get_install_dir() -> Path:
    # Dirs
    if not is_frozen():
        return Path(__file__).parent.parent  # Root of the project
    elif os.name == "nt":
        return Path(os.path.expandvars("%ProgramFiles(x86)%")) / PROGRAM_NAME

