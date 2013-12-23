from traits.api import HasTraits, Instance
from traitsui.api import View, Item
from chaco.api import VPlotContainer, ArrayPlotData, Plot
from enable.component_editor import ComponentEditor
from numpy import linspace, sin

class ContainerExample(HasTraits):

    plot = Instance(VPlotContainer)

    traits_view = View(Item('plot', editor=ComponentEditor(), show_label=False),
                       width=1000, height=600, resizable=True, title="Chaco Plot")

    def __init__(self):
        super(ContainerExample, self).__init__()

        x = linspace(-14, 14, 100)
        y = sin(x) * x**3
        plotdata = ArrayPlotData(x=x, y=y)

        scatter = Plot(plotdata)
        scatter.plot(("x", "y"), type="scatter", color="blue")

        line = Plot(plotdata)
        line.plot(("x", "y"), type="line", color="blue")

        container = VPlotContainer(scatter, line)
        self.plot = container

if __name__ == "__main__":
    ContainerExample().configure_traits()