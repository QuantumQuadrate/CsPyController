import sys, time
from PyQt4 import QtGui as qt
from PyQt4 import QtCore as qtcore
import random
import threading
import logging
logging.basicConfig(level=logging.DEBUG,
                    format='(%(threadName)-10s) %(message)s',
                    )
                    
app = qt.QApplication(sys.argv)
class widget(qtcore.QObject):
    def __init__(self, parent=None):
        qt.QWidget.__init__(self)

    def appinit(self):
        thread = worker()
        self.connect(thread, thread.signal, self.testfunc)
        thread.start()

    def testfunc(self, sigstr):
        logging.debug(sigstr)

class worker(qtcore.QThread):
    def __init__(self):
        qtcore.QThread.__init__(self, parent=app)
        self.signal = qtcore.SIGNAL("signal")
    def run(self):
        time.sleep(5)
        logging.debug("in thread")
        self.emit(self.signal, "hi from thread")

def main():
    w = widget()
    #w.show()
    qtcore.QTimer.singleShot(0, w.appinit)
    sys.exit(app.exec_())

main()