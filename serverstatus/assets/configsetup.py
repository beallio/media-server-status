import imp
import os
import logging
import logging.handlers as handlers

from serverstatus import app
from serverstatus.assets.exceptions import MissingConfigFile


def setup_logger():
    # setup application logger
    # use dir name thrice to return to base module path
    logger = None
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
    return logger


def load_config_file(logger=None):
    def gen_contents(config_data):
        # list module contents
        mods = dir(config_data)
        for obj in mods:
            # exclude objects that aren't our data
            if not obj.startswith('__'):
                # create dict object since flask app config only accepts dicts on updates
                result = {obj: getattr(config_data, obj)}
                yield result

    # import config file
    config_data = None
    config_location = '/var/test_data.py'
    try:
        config_data = imp.load_source('test_data', config_location)
        for data in gen_contents(config_data):
            app.config.update(data)
        if logger:
            logger.info('Config file loaded')
    except IOError:
        raise MissingConfigFile(config_location)
    return config_data


config = load_config_file(setup_logger())