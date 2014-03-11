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

import logging
logging.basicConfig(format='%(asctime)s %(threadName)s %(name)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

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
    with enaml.imports():
        from cs_GUI import Main
    app = QtApplication()
    main=Main(experiment=exp)
    main.show()
    main.maximize()
    main.send_to_front()
    main.activate_window()
    logger.info("starting application")
    app.start()

def new():
    exp=experiments.AQuA()
    #start in a new thread so you can continue to use the shell
    threading.Thread(target=guiThread,args=[exp]).start()
    return exp

if __name__ == '__main__':
    exp=experiments.AQuA()
    #start without creating a new thread
    guiThread(exp)
