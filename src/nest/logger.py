import os
import sys
import logging
import warnings
from typing import Callable

from nest.settings import settings


class ExceptionFilter(logging.Filter):
    """Avoid showing exceptions twice.
    """

    def filter(self, record: object) -> bool:
        return record.levelno != logging.ERROR


def setup_logger() -> logging.RootLogger:
    """Initialize logger.

    Returns:
        The global logger
    """

    # set up logger
    logger = logging.getLogger('Nest')
    logger.setLevel(logging.DEBUG)
    # create a formatter and add it to the handlers
    screen_formatter = logging.Formatter('%(message)s')
    # create a console handler
    screen_handler = logging.StreamHandler()
    screen_handler.setLevel(logging.INFO)
    screen_handler.setFormatter(screen_formatter)
    screen_handler.addFilter(ExceptionFilter())
    logger.addHandler(screen_handler)
    if settings['LOGGING_TO_FILE']:
        # create a file handler which logs warning and error messages
        file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler = logging.FileHandler(settings['LOGGING_PATH'], encoding='utf8')
        file_handler.setLevel(logging.WARNING)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def exception(func: Callable) -> Callable:
    """Decorator for logging errors and warnings of function.

    Parameters:
        func:
            The decorated function
    """

    def wrapper(*args, **kwargs):
        try:
            with warnings.catch_warnings(record=True) as warning_list:
                warnings.simplefilter('always')
                res = func(*args, **kwargs)
                for w in warning_list:
                    logger.warning(w.message)
            return res
        except Exception as exc_info:
            logger.exception(exc_info)
            raise

    return wrapper


# create global logger
logger = setup_logger()
