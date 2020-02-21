__author__ = 'Hexagon'

import ConfigParser
import os
import inspect
import logging
logger = logging.getLogger(__name__)
CONFIG_FILE = 'config/config.cfg'

def import_config():
    # import config file
    config = ConfigParser.ConfigParser()
    try:
        # This only works if the current working directory is never changed!!
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        config.read(os.path.join(path,CONFIG_FILE))
    except ConfigParser.NoSectionError:
        logger.critical('Could not find config file at %s', CONFIG_FILE)
    return config