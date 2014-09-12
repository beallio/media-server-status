import logging
from inspect import stack, getmodule


def logger(log_type):
    def log_decorator(func):
        def wrapped(*args, **kwargs):
            # preserve calling module name for logger
            frm = stack()[1]
            mod = getmodule(frm[0])
            logger = logging.getLogger(mod.__name__)
            logger.setLevel(log_type)
            result = func(*args, **kwargs)
            logger.debug(result)
            return result

        return wrapped

    return log_decorator


def log_args(function):
    def wrapper(*args, **kwargs):
        print 'Arguments:', args, kwargs
        return function(*args, **kwargs)

    return wrapper