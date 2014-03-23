#this files contains the workings to store a digital waveform and plot it using Matplotlib

from __future__ import division

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

import numpy

from atom.api import Atom, Range, Member, Bool, Typed, List
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp, EnumProp
from matplotlib.figure import Figure
from matplotlib.ticker import NullLocator, FixedLocator

defaultState=5

class Channel(Prop):
    active=Typed(BoolProp)
    
    def __init__(self,name,experiment,description=''):
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
    
    #def fromXML(self,xmlNode):
    #    #while self.listProperty: #go until the list is empty
    #    #    self.listProperty.pop()
    #    self.listProperty=[Channel('channel'+str(i),self.experiment,'').fromXML(child) for i, child in enumerate(xmlNode)]
    #    return self

class State(ListProp):
    digitalout=Member()
    allowedValues=[0,1,5]
    
    def __init__(self,experiment,digitalout):
        super(State,self).__init__('state',experiment,
            listProperty=[EnumProp('channel'+str(i),experiment,function=str(defaultState),allowedValues=self.allowedValues) for i in range(digitalout.numChannels)], #defaultState is a global at the top of the module
            listElementType=EnumProp,listElementName='channel',listElementKwargs={'function':str(defaultState),'allowedValues':self.allowedValues})
        self.digitalout=digitalout
    
    #def fromXML(self,xmlNode):
        #while self.listProperty: #go until the list is empty
        #    self.listProperty.pop()
        #self.listProperty=[EnumProp('channel'+str(i),self.experiment,function=str(defaultState),allowedValues=self.allowedValues).fromXML(child) for i, child in enumerate(xmlNode)] #defaultState is a global at the top of the module
        #return self

class Transition(Prop):
    time=Typed(FloatProp) #when does this transition happen
    digitalout=Member()
    state=Member()
    
    def __init__(self,name,experiment,digitalout=None,description=''):
        super(Transition,self).__init__(name,experiment,description)
        self.digitalout=digitalout
        self.time=FloatProp('time',self.experiment,'when this transition happens','0')
        self.state=State(self.experiment,self.digitalout)
        self.properties+=['time','state']

class Sequence(ListProp):
    digitalout=Member()
    
    def __init__(self,experiment,digitalout):
        super(Sequence,self).__init__('sequence',experiment,listElementType=Transition,listElementName='transition',listElementKwargs={'digitalout':digitalout})
        self.digitalout=digitalout
        
    #def fromXML(self,xmlNode):
    #    #while self.listProperty: #go until the list is empty
    #    #    self.listProperty.pop()
    #    self.listProperty=[Transition(self.experiment,self.digitalout).fromXML(child) for child in xmlNode]
    #    return self

class Waveform(Prop):
    
    #MPL plot
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    
    digitalout=Member()
    waveforms=Member()
    sequence=Member()
    isEmpty=Member()
    ax=Member()
    timeList=Member()
    stateList=Member()
    duration=Member()
    
    def __init__(self,name,experiment,digitalout,description='',waveforms=None):
        super(Waveform,self).__init__(name,experiment,description)
        self.digitalout=digitalout
        self.waveforms=waveforms
        self.sequence=Sequence(self.experiment,self.digitalout) #start with no transitions
        self.isEmpty=True
        self.properties+=['isEmpty','sequence']
        
        self.figure1=Figure(figsize=(5,5))
        self.figure2=Figure(figsize=(5,5))
        self.backFigure=self.figure2
        self.figure=self.figure1
        #self.updateFigure() #TODO: don't update on init, no data yet, update on evaluate
    
    def fromXML(self,xmlNode):
        super(Waveform,self).fromXML(xmlNode)
        self.updateFigure()
        return self
    
    def addTransition(self):
        #newTransition=Transition(self.experiment,self.digitalout)
        newTransition=self.sequence.add()
        self.updateFigure()
        return newTransition
    
    def format(self):
        '''Create timeList, a 1D array of transition times, and stateList a 2D array of output values.'''
        if len(self.sequence)==0:
            self.isEmpty=True
            self.timeList=numpy.zeros(0,dtype='uint64')
            self.stateList=numpy.zeros((0,self.digitalout.numChannels),dtype='uint8')
            self.duration=numpy.zeros(0,dtype='uint64')
        else:
            self.isEmpty=False
            
            #create arrays
            timeList=numpy.array([i.time.value for i in self.sequence],dtype='float64')
            stateList=numpy.array([[channel.value for channel in transition.state] for transition in self.sequence],dtype='uint8') #channel here refers to an IntProp, not to a Channel

            #convert to integral samples
            timeList=(timeList*self.digitalout.clockRate.value*self.digitalout.units.value).astype('uint64')

            #put the transition list in order
            order=numpy.argsort(timeList,kind='mergesort') #mergesort is slower than the default quicksort, but it is 'stable' which means items of the same value are kept in their relative order, which is desired here
            timeList=timeList[order]
            stateList=stateList[order]
            
            #if the waveform doesn't start with time 0, add it, and add defaultStates's to the beginning of statelist
            #LabView will modify the waveform in unpredictable ways if it doesn't start with time 0
            if timeList[0]>0:
                print 'inserting timelist 0'
                timeList=numpy.insert(timeList,0,0,axis=0)
                stateList=numpy.insert(stateList,0,defaultState,axis=0)
            
            #resolve 5's
            #set 5's in the first transition to 0
            for i in range(self.digitalout.numChannels):
                if stateList[0,i]==5:
                    stateList[0,i]=0
            #set other 5's to the prior state
            for i in range(1,len(timeList)):
                for j in range(self.digitalout.numChannels):
                    if stateList[i,j]==5:
                        stateList[i,j]=stateList[i-1,j]
            
            #remove redundant times
            #TODO:  If it becomes possible to send 5's to hardware, we will want to remove this section
            i=1 #start at 1 so we can compare to i-1=0
            while i<len(timeList):  #check list length each loop cycle, because it may get shorter
                if timeList[i-1]==timeList[i]:
                    timeList=numpy.delete(timeList,i-1,0) #remove the prior transition, because only the later one will stick anyway
                    stateList=numpy.delete(stateList,i-1,0)
                else:
                    i+=1 #if we deleted an item, the list position is advanced implicitly through the deletion of a prior element, and so we don't need to do this
                        
            self.timeList=timeList
            self.stateList=stateList
            
            # find the duration of each segment
            self.duration=timeList[1:]-timeList[:-1]
            self.duration=numpy.append(self.duration,1) #add in a 1 sample duration at end for last transition
    
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
    
    def drawMPL(self,stateList,timeList,duration):
        #draw on the inactive figure
        fig=self.backFigure
        
        #clear figure
        fig.clf()
        
        if not self.isEmpty:
        
            #get plot info
            numTransitions,numChannels=numpy.shape(stateList)
            
            #create axis
            ax=fig.add_subplot(111)
            ax.set_ylim(0,numChannels)
            ax.set_xlabel('samples')
            
            #create dummy lines for legend
            ax.plot((),(),linewidth=5,alpha=0.5,color='white',label='off 0')
            ax.plot((),(),linewidth=5,alpha=0.5,color='black',label='on 1')
            ax.plot((),(),linewidth=5,alpha=0.5,color='grey',label='unresolved 5')
            ax.plot((),(),linewidth=5,alpha=0.5,color='red',label='invalid')
            ax.legend(loc='upper center',bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=4)
            
            #make horizontal grid lines
            ax.grid(True)
            
            
            #create a timeList on the scale 0 to 1
            relativeTimeList=timeList/(timeList[-1]+1)
            relativeDuration=duration/(timeList[-1]+1)

            #Make a broken horizontal bar plot, i.e. one with gaps
            
            for i in xrange(numChannels):
                for j in xrange(numTransitions):
#                    ax.broken_barh(zip(timeList,duration),(i,0.8),facecolors=facecolors,linewidth=0)
                    if stateList[j,i]==1:
                        ax.axhspan(i+.1,i+.9, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='black',alpha=0.5)
                    elif stateList[j,i]==5:
                        ax.axhspan(i+.1,i+.9, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='grey',alpha=0.5)
                    elif stateList[j,i]>0:
                        ax.axhspan(i+.1,i+.9, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='red',alpha=0.5)
                    #do nothing on zero
            
            #tickList=self.timeList.copy()
            #tickList=numpy.array([timeList[0],timeList[-1]],dtype=float) #TODO: fix tick labeler so we don't have to do this
            tickList=numpy.insert(timeList,-1,timeList[-1]+1) #add one sample to the end
            #ax.xaxis.set_major_locator( FixedLocator(tickList) )
            #ax.xaxis.set_major_locator( NullLocator() )
            #ax.xaxis.set_minor_locator( NullLocator() )
            ax.set_xticks(tickList)
            ax.set_xlim(timeList[0],timeList[-1]+1)
        
            #make vertical tick labels on the bottom
            for label in ax.xaxis.get_ticklabels():
                label.set_rotation(90)
            
            ax.set_yticks(numpy.arange(numChannels)+0.5)
            ax.set_yticklabels([self.digitalout.channels[i].description+(' : ' if self.digitalout.channels[i].description else ' ')+str(i) for i in range(numChannels)])
        
            #make sure the tick labels have room
            fig.subplots_adjust(left=.2,right=.95,bottom=.2)
    
    def swapFigures(self):
        temp=self.backFigure
        self.backFigure=self.figure
        self.figure=temp
    
    def updateFigure(self):
        '''This function redraws the broken bar chart display of the waveform sequences.'''
        self.format() #update processed sequence
    
        #Make the matplotlib plot
        self.drawMPL(self.stateList,self.timeList,self.duration)
        
        try:
            deferred_call(self.swapFigures)
        except RuntimeError: #application not started yet
            self.swapFigures()
    
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
                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.stateList])+'</states>\n'+
                '</waveform>\n')
