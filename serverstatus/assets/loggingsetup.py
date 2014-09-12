import imp
import os
import logging

# import config file
config = imp.load_source('test_data', '/var/test_data.py')

# setup application logger
log_location = os.path.join(os.path.dirname(os.path.realpath(__file__)), '../tmp/status.log')
logger = logging.basicConfig(level=logging.DEBUG,
                             format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                             datefmt='%m-%d %H:%M',
                             filename=log_location,
                             filemode='a')


# file_handler = handlers.RotatingFileHandler(filename=log_location, maxBytes=3145728)
# file_handler.setLevel(logging.DEBUG)
#file_handler.setFormatter(
#    logging.Formatter(
#        '[%(levelname)s] %(asctime)s\n\tModule: %(module)s\n\tFunction: %(funcName)s \n\t%(message)s'))
#logger = logging.getLogger(__name__)
#logger.addHandler(file_handler)

