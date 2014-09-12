import imp
import os
import logging
import logging.handlers as handlers

# setup application logger
# use dir name thrice to return to base module path
log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'tmp')
print log_directory
log_location = os.path.join(log_directory, 'status.log')
if not os.path.isdir(log_directory):
    try:
        os.mkdir(log_directory)
    except IOError:
        pass
if os.path.isdir(log_directory):
    logging.basicConfig(level=logging.DEBUG,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M',
                        filemode='a')

    file_handler = handlers.RotatingFileHandler(filename=log_location, maxBytes=3145728)
    logging.getLogger('').addHandler(file_handler)
    logger = logging.getLogger(__name__)
    logger.debug('Logger initialized')
else:
    logger = None

# import config file
try:
    config = imp.load_source('test_data', '/var/test_data.py')
    if logger:
        logger.info('Config file loaded')
except IOError:
    if logger:
        logger.error('Config file not found')
    config = None
