from scipy.special import jn
from traits.api import HasTraits, Instance, Enum
from traitsui.api import View, Item
from chaco.api import Plot, ArrayPlotData,HPlotContainer
from chaco.tools.api import PanTool, ZoomTool
from enable.component_editor import ComponentEditor
from numpy import linspace, sin

class ConnectedRange(HasTraits):

    container = Instance(HPlotContainer)

    traits_view = View(Item('container', editor=ComponentEditor(),
                            show_label=False),
                       width=1000, height=600, resizable=True,
                       title="Connected Range")

    def __init__(self):
        x = linspace(-14, 14, 100)
        y = sin(x) * x**3
        plotdata = ArrayPlotData(x = x, y = y)

        scatter = Plot(plotdata)
        scatter.plot(("x", "y"), type="scatter", color="blue")

        line = Plot(plotdata)
        line.plot(("x", "y"), type="line", color="blue")

        self.container = HPlotContainer(scatter, line)

        scatter.tools.append(PanTool(scatter))
        scatter.tools.append(ZoomTool(scatter))

        line.tools.append(PanTool(line))
        line.tools.append(ZoomTool(line))

        #scatter.range2d = line.range2d
        scatter.index_range = line.index_range
        
if __name__ == "__main__":
    ConnectedRange().configure_traits()
