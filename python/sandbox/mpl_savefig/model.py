#enaml_mpl_thread_demo by Martin Lichtman

from atom.api import Atom, Typed
from matplotlib.figure import Figure
import os
import numpy
import logging
logger = logging.getLogger(__name__)
from enaml.application import deferred_call


class Model(Atom):

    #matplotlib figures
    figure = Typed(Figure)
    backFigure = Typed(Figure)
    figure1 = Typed(Figure)
    figure2 = Typed(Figure)

    def __init__(self):

        logger.info("Model.__init__()")

        #set up the matplotlib figures
        self.figure1 = Figure()
        self.figure2 = Figure()
        self.backFigure = self.figure2
        self.figure = self.figure1

    def get_figure_size(self):
        logger.info("Figure size: {}".format(self.figure.get_size_inches()))

    def get_dpi(self):
        logger.info("DPI: {}".format(self.figure.get_dpi()))

    def updatePlot(self):
        logger.info("Model.updatePlot()")
        fig = self.backFigure

        #clear the axis, or create a new one if none exists
        if len(fig.axes)>0:
            ax = fig.axes[0]
            ax.cla()
        else:
            ax = fig.add_subplot(111)

        #draw some stuff
        ax.plot(numpy.arange(4), numpy.random.rand(4))

        deferred_call(self.swapFigures)

    def swapFigures(self):
        temp = self.backFigure
        self.backFigure = self.figure
        self.figure = temp

    def set_size_inches(self, w, h):
        self.figure.set_size_inches(w, h)

    def set_dpi(self, dpi):
        self.figure.set_dpi(dpi)

    def save(self):
        i = 0
        filename = 'fig{}.pdf'.format(i)
        while os.path.exists(filename):
            i += 1
            filename = 'fig{}.pdf'.format(i)

        self.figure.savefig(filename, dpi=self.figure.get_dpi(), facecolor='w', edgecolor='w',
        orientation='portrait', papertype=None, format='pdf',
        transparent=True, bbox_inches=None, pad_inches=0,
        frameon=False)
