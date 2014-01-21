#this files contains the workings to store a digital waveform and plot it using Chaco

import numpy

from atom.api import Atom, Range, Member, Typed
#from traitsui.api import View, UItem, Item, Group, HGroup, VGroup, spring
from chaco.api import Plot, ArrayPlotData, PolygonPlot, OverlayPlotContainer
from enable.api import Component #, ComponentEditor

from atom.api import Bool, Typed
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import logging
logger = logging.getLogger(__name__)

from PyQt4 import QtCore
class signal_holder(QtCore.QObject):
    signal = QtCore.pyqtSignal()

class Channel(Prop):
    active=Typed(BoolProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(Channel,self).__init__(name,experiment,description)
        self.active=BoolProp('active',experiment,'','True')
        self.properties+=['active']

class Channels(ListProp):    
    digitalout=Member()
    
    def __init__(self,experiment,digitalout,description='A list of DAQmxPulse channels'):
        super(Channels,self).__init__('channels',experiment,description,
            listProperty=[Channel('channel'+str(i),experiment,'') for i in xrange(digitalout.numChannels)],
            listElementType=Channel,listElementName='channel')
        self.digitalout=digitalout
    
    def toHardware(self):
        #The actual IdleState and InitialState are all set to all X's, for continuity.
        activeChannels=[str(i) for i,c in enumerate(self.listProperty) if c.active.value]
        xState='X'*len(activeChannels)
        return ('<InitialState>'+xState+'</InitialState>\n<IdleState>'+xState+'</IdleState>\n<ActiveChannels>'+','.join(activeChannels)+'</ActiveChannels>\n')
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Channel(str(i),self.experiment,'').fromXML(child) for i, child in enumerate(xmlNode)]
        return self

class State(ListProp):
    digitalout=Member()
    
    def __init__(self,experiment,digitalout):
        super(State,self).__init__('state',experiment,
            listProperty=[IntProp('channel'+str(i),experiment,'','5') for i in range(digitalout.numChannels)],
            listElementType=IntProp)
        self.digitalout=digitalout
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[IntProp(str(i),self.experiment,'','5').fromXML(child) for i, child in enumerate(xmlNode)]
        return self

class Transition(Prop):
    time=Typed(FloatProp) #when does this transition happen
    digitalout=Member()
    state=Member()
    
    def __init__(self,experiment,digitalout,description=''):
        super(Transition,self).__init__('transition',experiment,description)
        self.digitalout=digitalout
        self.time=FloatProp('time',self.experiment,'when this transition happens','0')
        self.state=State(self.experiment,self.digitalout)
        self.properties+=['time','state']

class Sequence(ListProp):
    digitalout=Member()
    
    def __init__(self,experiment,digitalout):
        super(Sequence,self).__init__('sequence',experiment,listElementType=Transition)
        self.digitalout=digitalout
        
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Transition(self.experiment,self.digitalout).fromXML(child) for child in xmlNode]
        return self

class Waveform(Prop):
    
    #MPL plot
    #figure=Typed(plt.Figure)
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    refresh=Bool()

    #Chaco plot
    plot=Typed(Plot) #chaco plot
    component=Typed(Component)

    plotType='MPL'

    colors={0:'white',1:'black',5:'grey'} #color dictionary for plot
    
    digitalout=Member()
    waveforms=Member()
    sequence=Member()
    isEmpty=Member()
    ax=Member()
    timeList=Member()
    stateList=Member()
    duration=Member()
    
    #for refreshing the plot
    signal_holder = Typed(signal_holder)

    
    def __init__(self,name,experiment,digitalout,description='',waveforms=None):
        super(Waveform,self).__init__(name,experiment,description)
        self.digitalout=digitalout
        self.waveforms=waveforms
        self.sequence=Sequence(self.experiment,self.digitalout) #start with no transitions
        self.isEmpty=True
        self.properties+=['isEmpty','sequence']
        
        #set up the signal that allows to plot update to occur in the GUI thread
        self.signal_holder=signal_holder()
        self.signal_holder.signal.connect(self.swapFigures)
        
        if self.plotType=='chaco':
            #setup chaco plot
            self.plot=WaveformPlot()
            self.component=OverlayPlotContainer(self.plot)
            self.updateFigure()
        elif self.plotType=='MPL':
            self.figure1=Figure()
            self.figure2=Figure()
            self.backFigure=self.figure2
            self.figure=self.figure1
            self.updateFigure()
    
    def fromXML(self,xmlNode):
        super(Waveform,self).fromXML(xmlNode)
        self.updateFigure()
        return self
    
    def addTransition(self):
        newTransition=Transition(self.experiment,self.digitalout)
        self.sequence.append(newTransition)
        self.updateFigure()
        return newTransition
        
    def format(self):
        '''Create timeList, a 1D array of transition times, and stateList a 2D array of output values.'''
        if len(self.sequence)==0:
            self.isEmpty=True
            self.timeList=numpy.zeros(0,dtype=int)
            self.stateList=numpy.zeros((0,self.digitalout.numChannels),dtype='uint8')
            self.duration=numpy.zeros(0,dtype=int)
        else:
            self.isEmpty=False
            timeList=numpy.array([i.time.value for i in self.sequence])
            stateList=numpy.array([[channel.value for channel in transition.state] for transition in self.sequence],dtype='uint8') #channel here refers to an IntProp, not to a Channel
            #put the transition list in order
            order=timeList.argsort()
            #convert to samples
            self.timeList=numpy.array(timeList[order]*self.digitalout.clockRate.value,dtype=int) #convert to samples
            self.stateList=stateList[order]
            
            #if the waveform doesn't start with time 0, add it, and add 5's to the beginning of statelist
            #LabView will modify the waveform in unpredictable ways if it doesn't start with time 0
            if self.timeList[0]!=0:
                self.timeList=numpy.insert(self.timeList,0,0,axis=0)
                self.stateList=numpy.insert(self.stateList,0,5,axis=0)
            
            # find the duration of each segment
            self.duration=self.timeList[1:]-self.timeList[:-1]
            self.duration=numpy.append(self.duration,1) #add in a 1 sample duration at end for last transition

#    # dictionary version of colorMap, but we might not want to use this if it is slower
#    def colorMap(val):
#        '''The color map for plotting digitalout sequence bar charts.  Red indicates an invalid value.'''
#        return colors.get(val,'red')

    def colorMap(val):
        '''The color map for plotting digitalout sequence bar charts.  Red indicates an invalid value.'''
        if val==5:
            return 'grey'
        elif val==0:
            return 'white'
        elif val==1:
            return 'black'
        else:
            return 'red'
    
    #create a version of the colorMap function that can be passed arrays
    vColorMap=numpy.vectorize(colorMap) 
    
    def drawMPL(self,displayArray,data):
        #draw on the inactive figure
        fig=self.backFigure
        
        #clear figure
        fig.clf()

        #create axis
        ax=fig.add_subplot(111)
        ax.set_ylim(0,self.digitalout.numChannels)
        ax.set_xlabel('samples')
        
        #create dummy lines for legend
        ax.plot((),(),color='white',label='off 0')
        ax.plot((),(),color='black',label='on 1')
        ax.plot((),(),color='grey',label='unresolved 5')
        ax.plot((),(),color='red',label='invalid')
        ax.legend(loc='upper center',bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=4)
        
        if not self.isEmpty:
            #Make a broken horizontal bar plot, i.e. one with gaps
            for i in xrange(self.digitalout.numChannels):
                facecolors=self.vColorMap(displayArray[:,i]) #convert the digital values to colors
                ax.broken_barh(data,(i,0.8),facecolors=facecolors,linewidth=0)
            ax.set_xlim(self.timeList[0],self.timeList[-1]+1)
            tickList=self.timeList.copy()
            tickList=numpy.insert(self.timeList,-1,self.timeList[-1]+1) #add one sample to the end
            ax.set_xticks(tickList)
            ax.set_yticks(numpy.arange(self.digitalout.numChannels)+0.4)
            ax.set_yticklabels([str(i)+': '+self.digitalout.channels[i].description for i in range(self.digitalout.numChannels)])
    
    def swapFigures(self):
        temp=self.backFigure
        self.backFigure=self.figure
        self.figure=temp

    def updateFigure(self):
        '''This function redraws the broken bar chart display of the waveform sequences.'''
        self.format() #update processed sequence
        
        if not self.isEmpty:
            #resolve '5' unchanged samples
            displayArray=self.stateList.copy()
            for i in xrange(self.digitalout.numChannels): #for each channel
                for j in range(1,len(self.timeList)): #go through the sequence, but not the first item
                    if displayArray[j,i]==5:
                        displayArray[j,i]=displayArray[j-1,i] #change the '5' to be whatever was before it
        else:
            displayArray=None
        
        if self.plotType=='chaco':
            #Call the chaco plot
            self.plot.update(self.timeList,self.duration,displayArray)
        elif self.plotType=='MPL':
            data=zip(self.timeList,self.duration)
            #Make the matplotlib plot
            self.drawMPL(displayArray,data)
        
        #update the screen
        if self.plotType=='chaco':
            self.component=OverlayPlotContainer(self.plot)
        elif self.plotType=='MPL':
            self.signal_holder.signal.emit()
        
    def remove(self):
        if self.waveforms is not None:
            index=self.waveforms.remove(self) #remove ourselves from the master list, becoming subject to garbage collection
    
    def evaluate(self):
        super(Waveform,self).evaluate()
        self.updateFigure()
    
    def toHardware(self):
            self.format()
            return ('<waveform>'+
                '<name>'+self.name+'</name>'+
                '<transitions>'+' '.join([str(time) for time in self.timeList])+'</transitions>'+
                '<states>\n'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.stateList])+'\n</states>\n'+
                '</waveform>\n')

class WaveformPlot(Plot):
    '''A custom built Chaco plot to show waveforms.'''
    data=ArrayPlotData()
    colors={0:'white',1:'black',5:'grey'} #color dictionary for plot
    
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

