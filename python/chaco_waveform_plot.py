class WaveformPlot(Plot):
    '''A custom built Chaco plot to show waveforms.'''
    data=ArrayPlotData()
    
    def __init__(self):
        self.n=0
        #self.data=ArrayPlotData()
        super(WaveformPlot,self).__init__(self.data)
        self.colors={0:'white',1:'black',5:'grey'} #color dictionary for plot
        self.totalPlots=0
        
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
        
        #delete all previous plots
        if self.plots: #if it is not empty
            self.delplot(*self.plots.keys())
        
        # delete old arrays
        a=self.data.list_data()
        for i in a:
            self.data.del_data(i)
        
        #now add new ones
        numTransitions,numChannels=numpy.shape(states)
        for time in range(numTransitions):
            for channel in range(numChannels):
                if states[time,channel]==0:
                    #don't draw anything for the OFF state
                    pass
                else:
                    color=self.colors.get(states[time,channel],'red') #default to red if value is bad
                    self.rectangle(transitions[time],durations[time],channel,color)
        
        #set the plot limits to show all channels, even if they are off
        self.range2d.y_range.low = -.5
        self.range2d.y_range.high = numChannels -.5

# class ViewThing(HasTraits):
    # plot=Typed(WaveformPlot)
    
    # def _plot_default(self):
        # plot = WaveformPlot()
        # return plot
    
    # traits_view = View(
            # Group(
                # Item('plot',editor=ComponentEditor(),show_label=False),
            # orientation = "vertical"),
        # resizable=True, title='View thing')

# if __name__ == "__main__":
    # demo = ViewThing()
    # demo.plot.update(numpy.array([1,1.1,2,3.5]),numpy.array([.1,.9,1.5,.75]),
        # numpy.array([[1,1,0,5],[0,1,1,0],[1,5,7,0],[1,0,1,1]]))
    # demo.configure_traits()

