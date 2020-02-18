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
import cs_errors
import logging
cs_errors.setup_log()
logger = logging.getLogger(__name__)
import aqua


def guiThread(exp):
    logger.debug('importing GUI')
    with enaml.imports():
        from cs_GUI import Main
    logger.debug('starting GUI application')
    app = QtApplication()
    logger.debug('assigning experiment backend to GUI')
    main = Main(experiment=exp)
    # controller = Controller(exp=exp, view=main)

    logger.debug('gui show')
    main.show()
    logger.debug('gui activate')
    main.activate_window()
    logger.debug('gui to front')
    main.send_to_front()
    logger.debug('give the experiment a reference to the gui')
    exp.gui = main

    logger.info('starting QtApplication')
    app.start()


if __name__ == '__main__':
    logger.info('Started CsPyController')
    exp = aqua.AQuA()

    # start without creating a new thread
    guiThread(exp)
