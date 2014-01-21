import enaml
from enaml.qt.qt_application import QtApplication

#for button and taskbar icons
#from enaml.session import Session
#from cs_icons import CsIconProvider

import threading

import logging
logging.basicConfig(format='%(threadName)s %(name)s %(message)s', level=logging.DEBUG)
logger = logging.getLogger(__name__)

import model

if __name__ == '__main__':
    model=model.Model()
    with enaml.imports():
        from view import Main
    app = QtApplication()
    main=Main(model=model)
    main.show()
    logger.info("starting application")
    app.start()
