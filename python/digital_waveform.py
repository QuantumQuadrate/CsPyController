#this files contains the workings to store a digital waveform and plot it using Matplotlib

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

import numpy

from atom.api import Atom, Range, Member, Bool, Typed, List
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp, EnumProp
from matplotlib.figure import Figure

defaultState=0

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
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Channel(str(i),self.experiment,'').fromXML(child) for i, child in enumerate(xmlNode)]
        return self

class State(ListProp):
    digitalout=Member()
    allowedValues=[0,1,5]
    
    def __init__(self,experiment,digitalout):
        super(State,self).__init__('state',experiment,
            listProperty=[EnumProp('channel'+str(i),experiment,'',str(defaultState),allowedValues=self.allowedValues) for i in range(digitalout.numChannels)], #defaultState is a global at the top of the module
            listElementType=EnumProp,listElementKwargs={'allowedValues':self.allowedValues})
        self.digitalout=digitalout
    
    def fromXML(self,xmlNode):
        #while self.listProperty: #go until the list is empty
        #    self.listProperty.pop()
        self.listProperty=[EnumProp(str(i),self.experiment,'',str(defaultState),allowedValues=self.allowedValues).fromXML(child) for i, child in enumerate(xmlNode)] #defaultState is a global at the top of the module
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
            
            #create arrays
            timeList=numpy.array([i.time.value for i in self.sequence])
            stateList=numpy.array([[channel.value for channel in transition.state] for transition in self.sequence],dtype='uint8') #channel here refers to an IntProp, not to a Channel

            #convert to integral samples
            timeList=numpy.array(timeList*self.digitalout.clockRate.value,dtype=int)

            #put the transition list in order
            order=numpy.argsort(timeList,kind='mergesort') #mergesort is slower than the default quicksort, but it is 'stable' which means items of the same value are kept in their relative order, which is desired here
            timeList=timeList[order]
            stateList=stateList[order]
            
            #if the waveform doesn't start with time 0, add it, and add defaultStates's to the beginning of statelist
            #LabView will modify the waveform in unpredictable ways if it doesn't start with time 0
            if timeList[0]!=0:
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
        
        data=zip(self.timeList,self.duration)
        #Make the matplotlib plot
        self.drawMPL(displayArray,data)
        
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
