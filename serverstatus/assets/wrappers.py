"""
function wrappers module
"""

import logging
from inspect import stack, getmodule


def logger(log_type):
    """
    decorator to log output of functions
    :param log_type: logger level as string (debug, warn, info, etc)
    :type log_type: str
    """
    def log_decorator(func):
        """
        wrapped function
        """
        def wrapped(*args, **kwargs):
            # preserve calling module name for LOGGER
            frm = stack()[1]
            mod = getmodule(frm[0])
            wrapped_logger = logging.getLogger(mod.__name__)
            result = func(*args, **kwargs)
            try:
                getattr(wrapped_logger, log_type)(result)
            except AttributeError as err:
                wrapped_logger.error(err)
            return result

        return wrapped

    return log_decorator


def log_args(function):
    """
    Logs arguments passed to function
    """
    def wrapper(*args, **kwargs):
        print 'Arguments:', args, kwargs
        return function(*args, **kwargs)
    return wrapper