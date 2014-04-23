# Martin Lichtman
# created = 2013-04-03
# modified >= 2013-07-09

"""
cs.py

The cesium controller.  Handles user input/output, experiment flow control,
analysis, and TCP server for communication with LabView.
"""

#The following no longer applies now that:
#On Windows you must do "set ETS_TOOLKIT=qt4" from the command line before running this.
#The file cs.bat performs this task for you and then runs 'python cs.py'.

#The following is not supported until we figure out how to launch GUI from a background thread without it complaining.
#To run from a shell call: import cs; exp=cs.new()

import enaml
from enaml.qt.qt_application import QtApplication

#for button and taskbar icons
#from enaml.session import Session
#from cs_icons import CsIconProvider

import threading
import cs_errors
import logging
cs_errors.setup_log()
logger = logging.getLogger(__name__)
import experiments

#for icons
# class CsSession(Session):
    
    # def on_open(self):
        # global mainWindow
        # """ Override from enaml.session.Session to setup the windows and resources for the session."""
        # self.resource_manager.icon_providers['myicons'] = CsIconProvider()
        # with enaml.imports():
            # from cs_GUI import Main
        # mainWindow=Main()
        # mainWindow.experiment=exp
        # self.windows.append(mainWindow)

def guiThread(exp):
    logger.debug('importing GUI')
    with enaml.imports():
        from cs_GUI import Main
    app = QtApplication()
    main = Main(experiment=exp)
    #controller = Controller(exp=exp, view=main)

    main.show()
    main.activate_window()
    main.send_to_front()
    main.maximize()

    #give the experiment a reference to the gui
    exp.gui = main

    logger.debug('starting QtApplication')
    app.start()
    logger.info('Application active')

def new():
    logger.info('Started CsPyController')
    exp = experiments.AQuA()
    #start in a new thread so you can continue to use the shell
    threading.Thread(target=guiThread,args=[exp]).start()
    return exp

if __name__ == '__main__':
    logger.info('Started CsPyController')
    exp = experiments.AQuA()

    #start without creating a new thread
    guiThread(exp)
