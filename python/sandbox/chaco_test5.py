import enaml
from enaml.session import Session
from enaml.qt.qt_application import QtApplication
from traits.api import HasTraits, Instance, Array
import numpy

from enthought.chaco.api import ArrayPlotData, Plot
#from enthought.enable.api import Component

class CsSession(Session):
    def on_open(self):
        with enaml.imports():
            from gui import Main
        mainWindow=Main()
        mainWindow.AO=AO()
        self.windows.append(mainWindow)

class AO(HasTraits):
    plot=Instance(Plot)
    
    def __init__(self):
        x = numpy.linspace(-14, 14, 100)
        y = numpy.sin(x) * x**3
        plotdata = ArrayPlotData(x=x, y=y)

        plot = Plot(plotdata)
        plot.plot(("x", "y"), type="line", color="blue")
        plot.title = "sin(x) * x^3"

        self.plot=plot

if __name__ == '__main__':
    app = QtApplication([CsSession.factory('main')])
    app.start_session('main')
    app.start()