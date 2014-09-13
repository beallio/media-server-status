import logging
from inspect import stack, getmodule


def logger(log_type):
    def log_decorator(func):
        def wrapped(*args, **kwargs):
            # preserve calling module name for logger
            frm = stack()[1]
            mod = getmodule(frm[0])
            wrapped_logger = logging.getLogger(mod.__name__)
            result = func(*args, **kwargs)
            try:
                getattr(wrapped_logger, log_type)(result)
            except AttributeError as e:
                wrapped_logger.error(e)
            return result

        return wrapped

    return log_decorator


def log_args(function):
    def wrapper(*args, **kwargs):
        print 'Arguments:', args, kwargs
        return function(*args, **kwargs)

    return wrapper