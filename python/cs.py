# Martin Lichtman
# created = 2013-04-03
# modified >= 2013-07-09

"""
cs.py

The cesium controller.  Handles user input/output, experiment flow control,
analysis, and TCP server for communication with LabView.

On Windows you must do "set ETS_TOOLKIT=qt4" from the command line before running this.
The file cs.bat performs this task for you and then runs 'python cs.py'.

To run from a shell call: import cs; exp,app=cs.new()
"""

print """On Windows you must do "set ETS_TOOLKIT=qt4" from the command line before running this.
The file cs.bat performs this task for you and then runs 'python cs.py'.
On OS X you must do "export ETS_TOOLKIT=qt4" from the command line before running this.

To run from a shell call: import cs; exp,app=cs.new()
"""


import enaml
from enaml.qt.qt_application import QtApplication

#for button and taskbar icons
#from enaml.session import Session
#from cs_icons import CsIconProvider

#import threading

import logging
logging.basicConfig(format='%(asctime)s %(name)s %(levelname)s %(message)s', datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
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

def new():
    #global exp
    exp=experiments.AQuA()
    #app = QtApplication([CsSession.factory('main')])
    with enaml.imports():
        from cs_GUI import Main
    app = QtApplication()
    #app.start_session('main')
    main=Main(experiment=exp)
    main.show()
    app.start()
    #threading.Thread(target=app.start).start()
    return exp, app

if __name__ == '__main__':
    logger.info('starting application')
    exp,app=new()
    # The GUI goes not appear and the app exits immediately without this line when not
    # run from a python shell.
    #app.start() #standalone mode
