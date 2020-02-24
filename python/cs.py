#!/usr/bin/env python
# created = 2013-04-03
# modified >= 2013-07-09

"""
cs.py

The cesium controller.  Handles user input/output, experiment flow control,
analysis, and TCP server for communication with LabView.
"""
__author__ = 'Martin Lichtman'

import enaml
from enaml.qt.qt_application import QtApplication
import logging
import logging.handlers
import colorlog
import aqua
import os
import inspect
import ConfigParser
from cs_errors import PauseError


def setup_log():
    """
    This function sets up the error logging to both console and file. Logging
    can be set up at the top of each file by doing:
    import logging
    logger = logging.getLogger(__name__)
    """

    # get the root logger
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # set up logging to console for INFO and worse
    sh = colorlog.StreamHandler()
    sh.setLevel(logging.INFO)

    sh_formatter = colorlog.ColoredFormatter("%(log_color)s%(levelname)-8s - "
                                             "%(name)-25s - %(threadName)-15s -"
                                             " %(asctime)s - %(cyan)s \n  "
                                             "%(message)s\n",
                                             datefmt=None,
                                             reset=True,
                                             log_colors={
                                                         'DEBUG':    'cyan',
                                                         'INFO':     'green',
                                                         'WARNING':  'yellow',
                                                         'ERROR':    'red',
                                                         'CRITICAL': 'red,'
                                                                     'bg_white',
                                                         },
                                             secondary_log_colors={},
                                             style='%'
                                             )
    sh.setFormatter(sh_formatter)

    # This only works if the current working directory is never changed!!
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    # set up logging to file for ALL messages
    fh = logging.handlers.TimedRotatingFileHandler(
        os.path.join(path, '__project_cache__/log.txt'),
        when='midnight',
        interval=1,
        backupCount=7)
    fh.setLevel(logging.INFO)
    fh_formatter = logging.Formatter(fmt='%(asctime)s.%(msecs)03d - %(threadNam'
                                         'e)s - %(filename)s.%(funcName)s.%(lin'
                                         'eno)s - %(levelname)s\n%(message)s\n'
                                         '\n', datefmt='%Y/%m/%d %H:%M:%S')
    fh.setFormatter(fh_formatter)

    # put the handlers to use
    logger.addHandler(sh)
    logger.addHandler(fh)


def import_config():
    # import config file
    logger = logging.getLogger(__name__)
    CONFIG_FILE = 'config/config.cfg'
    configuration = ConfigParser.ConfigParser()
    try:
        # This only works if the current working directory is never changed!!
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        configuration.read(os.path.join(path, CONFIG_FILE))
    except ConfigParser.NoSectionError:
        logger.critical('Could not find config file at %s', CONFIG_FILE)
        raise PauseError
    return configuration


def guiThread(exp):
    logger = logging.getLogger(__name__)
    logger.debug('importing GUI')
    with enaml.imports():
        from cs_GUI import Main
    logger.debug('starting GUI application')
    app = QtApplication()
    logger.debug('assigning experiment backend to GUI')
    main = Main(experiment=exp)

    logger.debug('give the experiment a reference to the gui')
    exp.gui = main

    logger.debug('gui show')
    main.show()
    logger.debug('gui activate')
    main.activate_window()
    logger.debug('gui to front')
    main.send_to_front()
    logger.info('Launching GUI Application')
    app.start()


if __name__ == '__main__':
    setup_log()
    logger = logging.getLogger(__name__)
    logger.info('Starting up CsPyController...')
    logger.info('looking for config file')
    config = import_config()
    logger.info('Found config.. Making experiment')
    exp = aqua.AQuA(config=config)
    logger.info('Experiment built, building GUI')
    # start without creating a new thread
    guiThread(exp)
