import imp
import os
import logging
import logging.handlers as handlers

from flask import Flask
from flask_images import Images


app = Flask(__name__)
app.secret_key = 'monkey'
images = Images(app)
app.config.update(
    APPNAME='server_status',
    LOGGINGMODE=logging.DEBUG,
    APPLOCATION=os.path.join(os.path.dirname(os.path.dirname(
        os.path.realpath(__file__)))))
app.config['APP_MODULESLOCATION'] = os.path.join(app.config['APPLOCATION'],
                                                 'serverstatus')

import views
import assets
from assets.exceptions import MissingConfigFile
from assets.services import SubSonic


def _setup_logger():
    """
    Setup application logging object

    :return: logging object
    """
    mod_logger = None
    # use dir name thrice to return to base module path
    # log_directory = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__)))), 'tmp')
    log_directory = os.path.join('/var', 'tmp')
    log_location = os.path.join(log_directory,
                                '_'.join([app.config['APPNAME'], 'status.log']))
    if not os.path.isdir(log_directory):
        try:
            os.mkdir(log_directory)
        except IOError:
            pass
    if os.path.isdir(log_directory):
        file_handler = handlers.RotatingFileHandler(filename=log_location,
                                                    maxBytes=3145728)
        formatter = logging.Formatter(
            '%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
            "%Y-%m-%d %H:%M:%S")
        file_handler.setFormatter(formatter)
        logging.getLogger('').addHandler(file_handler)
        mod_logger = logging.getLogger(__name__)
        mod_logger.setLevel(app.config['LOGGINGMODE'])
        mod_logger.debug('logger initialized at {}'.format(log_location))
    return mod_logger


def _load_config_file(mod_logger=None):
    def gen_contents(config_data):
        # list module contents
        """
        Generator to return modules from config file
        :type config_data: __builtin__.module
        """
        mods = dir(config_data)
        for config_attrib in mods:
            # exclude objects that aren't our data
            if not config_attrib.startswith('__'):
                # create dict object since flask app config only accepts dicts on updates
                config_value = getattr(config_data, config_attrib)
                if config_attrib in app.config:
                    mod_logger.warning(
                        'Overwriting existing config value {} with {}'.format(
                            config_attrib, config_value))
                result = {config_attrib: config_value}
                yield result

    # import config file
    config_data_file = None
    config_location = '/var/test_data.py'
    try:
        config_data_file = imp.load_source('test_data', config_location)
        for data in gen_contents(config_data_file):
            app.config.update(data)
        if mod_logger:
            mod_logger.info(
                'Config file loaded from {}'.format(config_location))
    except IOError as e:
        errs = dict(err=e.strerror, dir_location=config_location)
        logger_msg = '{err}: Configuration file could not be found at "{dir_location}"'.format(
            **errs)
        mod_logger.critical(logger_msg)
        raise MissingConfigFile(logger_msg)


# initialize logger
logger = _setup_logger()

# import config data from config file into flask app object
_load_config_file(logger)

# remove initialization functions from namespace
del _load_config_file
del _setup_logger
