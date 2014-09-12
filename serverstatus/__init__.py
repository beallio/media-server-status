import imp
import os
import logging
import logging.handlers as handlers

from flask import Flask


app = Flask(__name__)
app.config.update(
    APPNAME='server_status',
    LOGGINGMODE=logging.DEBUG,
    APPLOCATION=os.path.join(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))))
app.config['APP_MODULESLOCATION'] = os.path.join(app.config['APPLOCATION'], 'serverstatus')

import views
import assets
from assets.exceptions import MissingConfigFile


def _setup_logger():
    # setup application mod_logger
    # use dir name thrice to return to base module path
    logger = None
    log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'tmp')
    log_location = os.path.join(log_directory, '_'.join([app.config['APPNAME'], 'status.log']))
    if not os.path.isdir(log_directory):
        try:
            os.mkdir(log_directory)
        except IOError:
            pass
    if os.path.isdir(log_directory):
        file_handler = handlers.RotatingFileHandler(filename=log_location, maxBytes=3145728)
        formatter = logging.Formatter('%(asctime)s %(name)-12s %(levelname)-8s %(message)s', "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(file_handler)
        logger = logging.getLogger(__name__)
        logger.setLevel(app.config['LOGGINGMODE'])
        logger.debug('Logger initialized at {}'.format(log_location))
    return logger


def _load_config_file(logger=None):
    def gen_contents(config_data):
        # list module contents
        mods = dir(config_data)
        for config_attrib in mods:
            # exclude objects that aren't our data
            if not config_attrib.startswith('__'):
                # create dict object since flask app config only accepts dicts on updates
                config_value = getattr(config_data, config_attrib)
                if config_attrib in app.config:
                    logger.warning('Overwriting existing config value {} with {}'.format(config_attrib, config_value))
                result = {config_attrib: config_value}
                yield result

    # import config file
    config_data = None
    config_location = '/var/test_data.py'
    try:
        config_data = imp.load_source('test_data', config_location)
        for data in gen_contents(config_data):
            app.config.update(data)
        if logger:
            logger.info('Config file loaded from {}'.format(config_location))
    except IOError as e:
        errs = dict(err=e.strerror, dir_location=config_location)
        logger_msg = '{err}: Configuration file could not be found at "{dir_location}"'.format(**errs)
        logger.critical(logger_msg)
        raise MissingConfigFile(logger_msg)
    return config_data


# load config data and initialize mod_logger
mod_logger = _setup_logger()
_load_config_file(mod_logger)
# remove initialization functions from namespace
del _load_config_file
del _setup_logger
