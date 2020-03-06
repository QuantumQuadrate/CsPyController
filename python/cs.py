#!/usr/bin/env python
# created = 2013-04-03
# modified >= 2013-07-09

"""
cs.py

The cesium controller.  Handles user input/output, experiment flow control,
analysis, and TCP server for communication with LabView.
"""
__author__ = 'Martin Lichtman'


def setup_logging_handlers():
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


def get_config_from_location(config_location):
    """
    Loads a configuration file from a specified location.
    """
    logger = logging.getLogger(__name__)
    configuration = ConfigParser.ConfigParser()
    try:
        # This only works if the current working directory is never changed!!
        filename = inspect.getframeinfo(inspect.currentframe()).filename
        path = os.path.dirname(os.path.abspath(filename))
        configuration.read(os.path.join(path, config_location))
    except ConfigParser.NoSectionError:
        logger.critical('Could not find config file at %s', config_location)
        raise PauseError
    return configuration


def launch_gui_with_experiment(experiment):
    """
    Launches the GUI with a specific instance of the Experiment class
    """
    logger = logging.getLogger(__name__)
    logger.debug('importing GUI')
    with enaml.imports():
        from cs_GUI import Main
    logger.debug('starting GUI application')
    app = QtApplication()
    logger.debug('assigning experiment backend to GUI')
    main = Main(experiment=experiment)

    logger.debug('give the experiment a reference to the gui')
    experiment.gui = main

    logger.debug('gui show')
    main.show()
    logger.debug('gui activate')
    main.activate_window()
    logger.debug('gui to front')
    main.send_to_front()
    logger.info('Launching GUI Application')
    app.start()


if __name__ == '__main__':
    import logging
    import logging.handlers
    import os
    import inspect
    import enaml
    import ConfigParser
    import colorlog
    from enaml.qt.qt_application import QtApplication
    from cs_errors import PauseError
    from ConfigInstrument import Config
    import h5py

    setup_logging_handlers()
    logger = logging.getLogger(__name__)
    logger.info('Starting up CsPyController...')

    logger.info('looking for config file')
    # This only works if the current working directory is never changed!!
    filename = inspect.getframeinfo(inspect.currentframe()).filename
    path = os.path.dirname(os.path.abspath(filename))
    config_instrument_name = 'Config'
    # Initially we have a ConfigInstrument that doesn't know which Experiment it
    # is a part of.
    config_instrument = Config(name=config_instrument_name,
                               experiment=None,
                               description='Configuration File',
                               config=get_config_from_location(
                                   os.path.join(path, 'config\\config.cfg'))
                               )
    # The instrument can however resolve whether we want to use the config file
    # or the saved config from the previous experiment before choosing an
    # experiment.
    logger.info('Found config.. Checking that it matches with settings...')
    # This only works if the current working directory is never changed!!
    cache_location = os.path.join(path, '__project_cache__\\')
    settings_location = os.path.join(cache_location, 'settings.hdf5')
    temp_location = os.path.join(cache_location, 'previous_settings.hdf5')
    with h5py.File(name=settings_location, mode='r+') as hdf:
        group = hdf['settings/experiment']
        config_instrument.fromHDF5(group.attrs[config_instrument_name])
        config_instrument.toHDF5(group)

    logger.info('Config finalized.. Making experiment according to config')
    # Now that we have a choice of config, we can import and construct different
    # Experiment child classes unique to your experiment. This allows each
    # experiment to only have the instruments, analyses, properties, and so on
    # that are relevant to them, and can choose from all the available ones
    # defined in the code base.
    experiment_name = config_instrument.config.get('EXPERIMENT', 'Name')
    experiment_args = {
        'config_instrument': config_instrument,
        'cache_location': cache_location,
        'settings_location': settings_location,
        'temp_location': temp_location
    }
    if experiment_name == 'FNODE':
        import fnode
        experiment = fnode.FNODE(**experiment_args)
    elif experiment_name == 'Hybrid':
        import hybrid
        experiment = hybrid.Hybrid(**experiment_args)
    else:
        import aqua
        experiment = aqua.AQuA(**experiment_args)
    logger.info('Experiment built, building GUI')
    launch_gui_with_experiment(experiment)
