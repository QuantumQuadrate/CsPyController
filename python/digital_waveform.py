#this files contains the workings to display a digital waveform plot using Chaco

import numpy

from traits.api import HasTraits, Instance, Range
from traitsui.api import View, UItem, Item, Group, HGroup, VGroup, spring
from chaco.api import Plot, ArrayPlotData, PolygonPlot
from enable.api import ComponentEditor

class WaveformPlot(Plot):
    #plot=Instance(Plot)
    data=Instance(ArrayPlotData)
    
    def __init__(self):
        self.n=0
        self.data=ArrayPlotData()
        #self.plot = Plot(self.data, title='Waveform Chart')
        super(WaveformPlot,self).__init__(self.data)
        self.title='View thing'
    
    def rectangle(self,transition,duration,channel,color):
        n=self.n
        xarray=numpy.array([transition,transition+duration,transition+duration,transition])
        yarray=numpy.array([channel+.4,channel+.4,channel-.4,channel-.4])
        self.data.set_data('x'+str(n),xarray)
        self.data.set_data('y'+str(n),yarray)
        self.plot(('x'+str(n),'y'+str(n)),
            type='polygon',face_color=color, edge_color='transparent')
        self.n+=1
    
    def update(self,transitions,durations,states):
        '''transitions is an array of transition start times.
        durations is an array of transition time duration.
        states is a 2D array of size len(transitions)*len(channels) containing 
        the state of each channel at each time'''
        
        # first delete old arrays
        for d in self.data.list_data():
            self.data.del_data(d)
        self.n=0
        
        #now add new ones
        numTransitions,numChannels=numpy.shape(states)
        for i in range(numTransitions):
            for j in range(numChannels):
                if states[i,j]==0:
                    #don't draw anything for the OFF state
                    pass
                elif states[i,j]==1:
                    self.rectangle(transitions[i],durations[i],j,'black')
                elif states[i,j]==5:
                    self.rectangle(transitions[i],durations[i],j,'grey')
                else:
                    self.rectangle(transitions[i],durations[i],j,'red')

class ViewThing(HasTraits):
    plot=Instance(WaveformPlot)
    
    def _plot_default(self):
        plot = WaveformPlot()
        return plot
    
    traits_view = View(
            Group(
                Item('plot',editor=ComponentEditor(),show_label=False),
            orientation = "vertical"),
        resizable=True, title='View thing')

if __name__ == "__main__":
    demo = ViewThing()
    demo.plot.update(numpy.array([1,1.1,2,3.5]),numpy.array([.1,.9,1.5,.75]),
        numpy.array([[1,1,0,5],[0,1,1,0],[1,5,7,0],[1,0,1,1]]))
    demo.configure_traits()

