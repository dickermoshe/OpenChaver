import functools
import logging
import time

logger = logging.getLogger(__name__)

def restart_on_exception(f, delay=1, exception=Exception):  # pragma: no cover
    @functools.wraps(f)
    def g(*args, **kwargs):
        while True:
            try:
                f(*args, **kwargs)
            except exception:
                logger.exception(f"{f.__name__} crashed due to exception, restarting.")
                time.sleep(
                    delay
                )  # To prevent extremely fast restarts in case of bad state.

    return g


def handle_error(func):
    def __inner(*args, **kwargs):
        # Set the attribute to the function name
        __inner.__name__ = func.__name__

        try:
            return func(*args, **kwargs)
        except:  # noqa: E722
            logger.exception(f"Exception in {func.__name__}")
            raise

    return __inner
