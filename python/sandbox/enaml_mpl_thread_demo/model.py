#enaml_mpl_thread_demo by Martin Lichtman

from atom.api import Atom, Typed
from PyQt4 import QtCore
from matplotlib.figure import Figure
import numpy
import time
import logging
logger = logging.getLogger(__name__)

class goThread(QtCore.QThread):
    def __init__(self,model):
        logger.info("goThread.__init__()")
        super(goThread,self).__init__()
        self.model=model
    
    def run(self):
        logger.info("goThread.run()")
        self.model.go()

class signal_holder(QtCore.QObject):
    signal = QtCore.pyqtSignal()

class Model(Atom):

    goThread=Typed(goThread)
    signal_holder=Typed(signal_holder)
    figure=Typed(Figure)
    realFigure=Typed(Figure)
    blankFigure=Typed(Figure)

    def __init__(self):
        logger.info("Model.__init__()")
        #pass this Experiment instance into the goThread, so it can refer back here in it's run() method
        self.goThread=goThread(self)

        #set up the signal that allows the plot update to occur in the GUI thread
        self.signal_holder=signal_holder()
        self.signal_holder.signal.connect(self.swapFigures)

        #create two figures, so we can swap back and forth for low-resource refreshes
        self.realFigure=Figure()
        self.blankFigure=Figure()

    def go(self):
        logger.info("Model.go()")
        #do some time consuming stuff
        time.sleep(3)
        #then redraw the figure
        self.updatePlot()

    def updatePlot(self):
        logger.info("Model.updatePlot()")
        fig=self.realFigure

        #clear the axis, or create a new one if none exists
        if len(fig.axes)>0:
            ax=fig.axes[0]
            ax.cla()
        else:
            ax=fig.add_subplot(111)

        #draw some stuff
        ax.plot(numpy.arange(4),numpy.random.rand(4))

        #signal the GUI thread to update the graph
        self.signal_holder.signal.emit()

    def swapFigures(self):
        logger.info("Model.swapFigures()")
        '''Trick Enaml into redrawing the figure by swapping the bound figure.'''
        self.figure=self.blankFigure
        self.figure=self.realFigure