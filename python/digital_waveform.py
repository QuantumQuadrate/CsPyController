#this files contains the workings to store a digital waveform and plot it using Matplotlib

from __future__ import division
import logging
logger = logging.getLogger(__name__)

from atom.api import Member, Typed
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, FloatProp, ListProp, EnumProp, Numpy1DProp, Numpy2DProp
from matplotlib.figure import Figure
import numpy, h5py

defaultState = 5


class Channel(Prop):
    active = Typed(BoolProp)
    
    def __init__(self, name, experiment, description=''):
        super(Channel, self).__init__(name, experiment, description)
        self.active = BoolProp('active', experiment, '', 'True')
        self.properties += ['active']


class Channels(ListProp):
    digitalout = Member()
    
    def __init__(self, experiment, digitalout, description='A list of HSDIO output channels'):
        super(Channels, self).__init__('channels', experiment, description,
            listProperty=[Channel('channel'+str(i), experiment, '') for i in xrange(digitalout.numChannels)],
            listElementType=Channel, listElementName='channel')
        self.digitalout = digitalout
    
    def toHardware(self):
        #The actual IdleState and InitialState are all set to all X's, for continuity.
        activeChannels = [str(i) for i, c in enumerate(self.listProperty) if c.active.value]
        xState = 'X'*len(activeChannels)
        return '<InitialState>'+xState+'</InitialState>\n<IdleState>'+xState+'</IdleState>\n<ActiveChannels>'+','.join(activeChannels)+'</ActiveChannels>\n'


class State(ListProp):
    digitalout = Member()
    allowedValues = [0, 1, 5]
    
    def __init__(self,experiment,digitalout):
        super(State,self).__init__('state',experiment,
            listProperty=[EnumProp('channel'+str(i),experiment,function=str(defaultState),allowedValues=self.allowedValues) for i in range(digitalout.numChannels)], #defaultState is a global at the top of the module
            listElementType=EnumProp,listElementName='channel',listElementKwargs={'function':str(defaultState),'allowedValues':self.allowedValues})
        self.digitalout=digitalout


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
    figure = Typed(Figure)
    backFigure = Typed(Figure)
    figure1 = Typed(Figure)
    figure2 = Typed(Figure)
    
    digitalout = Member()
    waveforms = Member()
    sequence = Member()
    isEmpty = Member()
    ax = Member()
    timeList = Member()
    stateList = Member()
    duration = Member()
    
    def __init__(self, name, experiment, description='', digitalout=None, waveforms=None):
        super(Waveform,self).__init__(name, experiment, description)
        self.digitalout = digitalout
        self.waveforms = waveforms
        self.sequence = Sequence(self.experiment, self.digitalout)  # start with no transitions
        self.isEmpty = True
        self.properties += ['isEmpty', 'sequence']
        
        self.figure1 = Figure(figsize=(5, 5))
        self.figure2 = Figure(figsize=(5, 5))
        self.backFigure = self.figure2
        self.figure = self.figure1
    
    def fromXML(self, xmlNode):
        super(Waveform, self).fromXML(xmlNode)
        self.updateFigure()
        return self
    
    def addTransition(self):
        #newTransition=Transition(self.experiment,self.digitalout)
        newTransition = self.sequence.add()
        self.updateFigure()
        return newTransition
    
    def fmt(self): #format is a python built-in so I did not want to use that as a function name
        """Create timeList, a 1D array of transition times, and stateList a 2D array of output values."""
        if len(self.sequence)==0:
            self.isEmpty = True
            self.timeList = numpy.zeros(0, dtype='uint64')
            self.stateList = numpy.zeros((0, self.digitalout.numChannels), dtype='uint8')
            self.duration = numpy.zeros(0, dtype='uint64')
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
            self.duration=numpy.append(self.duration,numpy.array(1,dtype=numpy.uint64)) #add in a 1 sample duration at end for last transition
    
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
            tickList=numpy.append(timeList,numpy.array(timeList[-1]+1,dtype=numpy.uint64)) #add one sample to the end
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
        self.fmt() #update processed sequence
    
        #Make the matplotlib plot
        self.drawMPL(self.stateList,self.timeList,self.duration)
        
        try:
            deferred_call(self.swapFigures)
        except RuntimeError: #application not started yet
            self.swapFigures()
    
    def remove(self):
        if self.waveforms is not None:
            self.waveforms.remove(self) #remove ourselves from the master list, becoming subject to garbage collection
    
    def evaluate(self):
        if self.experiment.allow_evaluation:
            super(Waveform,self).evaluate()
            self.updateFigure()
    
    def toHardware(self):
            self.fmt()
            return ('<waveform>'+
                '<name>'+self.name+'</name>'+
                '<transitions>'+' '.join([str(time) for time in self.timeList])+'</transitions>'+
                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.stateList])+'</states>\n'+
                '</waveform>\n')

    def toHDF5(self,hdf_parent_node,name=None):
        #special toHDF5 method to ease compatability to new numpy based waveforms
        try:
            my_node=hdf_parent_node.create_group(name)
        except:
            print 'trouble with my_node=hdf_parent_node.create_group(name)'
        
        try:
            trans=numpy.array([(t.description,t.time.function,t.time.value) for t in self.sequence],dtype=[('description',object),('function',object),('value',numpy.float64)])
        except:
            print "trouble with trans=numpy.array([(t.time.description,t.time.function,t.time.value) for t in self.sequence],dtype=[('description',object),('function',object),('value',numpy.float64)])"
        try:
            my_node.create_dataset('transitions', data=trans, dtype=[('description', h5py.special_dtype(vlen=str)), ('function', h5py.special_dtype(vlen=str)), ('value', numpy.float64)])
        except:
            print "trouble with my_node.create_dataset('transitions',data=trans,dtype=[('description',h5py.special_dtype(vlen=str)),('function',h5py.special_dtype(vlen=str)),('value',numpy.float64)])"

        try:
            seq=numpy.array([[(c.function,c.value) for c in t.state] for t in self.sequence],dtype=[('function',object),('value',numpy.uint8)])
        except:
            print "trouble with seq=numpy.array([[(c.function,c.value) for c in t.state] for t in self.sequence],dtype=[('function',object),('value',numpy.uint8)])"
        try:
            my_node.create_dataset('sequence',data=seq,dtype=[('function',h5py.special_dtype(vlen=str)),('value',numpy.uint8)])
        except:
            print "trouble with my_node.create_dataset('sequence',data=seq,dtype=[('function',h5py.special_dtype(vlen=str)),('value',numpy.uint8)])"
    

class NumpyChannels(Numpy1DProp):
    digitalout = Member()
    
    def __init__(self, experiment, digitalout, description=''):
        super(NumpyChannels, self).__init__('channels', experiment, description, dtype=[('description', object), ('function', object), ('value', bool)], hdf_dtype=[('description', h5py.special_dtype(vlen=str)), ('function', h5py.special_dtype(vlen=str)), ('value', bool)], zero=('new', 'True', True))
        self.digitalout = digitalout

    def toHardware(self):

        #create a list of active channel numbers
        active_channels = numpy.arange(len(self.array))[self.array['value']]
        active_channels_str = ','.join(map(str, active_channels))

        #The actual IdleState and InitialState are all set to all X's, for continuity.
        #We just need the right number of X's corresponding to the number of channels
        x_state = 'X'*len(active_channels)

        return '<InitialState>{}</InitialState>\n<IdleState>{}</IdleState>\n<ActiveChannels>{}</ActiveChannels>\n'.format(x_state, x_state, active_channels_str)


class NumpyTransitions(Numpy1DProp):
    def __init__(self, experiment, description=''):
        super(NumpyTransitions, self).__init__('transitions', experiment, description, dtype=[('description', object), ('function', object), ('value', numpy.float64)], hdf_dtype=[('description', h5py.special_dtype(vlen=str)), ('function', h5py.special_dtype(vlen=str)), ('value', numpy.float64)], zero=('new', '0', 0))

    def evaluate(self):
        for x in self.array:
            x['value'] = numpy.float64(self.experiment.eval_general(x['function']))

    def copy(self):
        new=NumpyTransitions(self.experiment,self.description)
        new.dtype=self.dtype
        new.hdf_dtype=self.hdf_dtype
        new.zero=self.zero
        new.array=self.array.copy()
        return new

class NumpySequence(Numpy2DProp):
    def __init__(self, experiment, description=''):
        super(NumpySequence, self).__init__('sequence', experiment, description, dtype=[('function', object), ('value', numpy.uint8)], hdf_dtype=[('function', h5py.special_dtype(vlen=str)), ('value', numpy.uint8)], zero=('', 5))

    def evaluate(self):
        for row in self.array:
            for x in row:
                temp = self.experiment.eval_general(x['function'])
                if (temp == 0) or (temp == 1):
                    x['value'] = temp
                else:
                    x['value'] = 5
    
    def copy(self):
        new=NumpySequence(self.experiment,self.description)
        new.dtype=self.dtype
        new.hdf_dtype=self.hdf_dtype
        new.zero=self.zero
        new.array=self.array.copy()
        return new

class NumpyWaveform(Prop):
    
    #MPL plot
    figure=Typed(Figure)
    backFigure=Typed(Figure)
    figure1=Typed(Figure)
    figure2=Typed(Figure)
    
    waveforms=Member() #the parent
    digitalout=Member() #the DAQmxDO or HSDIO
    channelList=Member() #holds the channel number for each column of sequence (not all channels need be present, they will be filled in as zeros)
    transitions=Member()
    sequence=Member()
    isEmpty=Member()
    ax=Member()
    timeList=Member()
    stateList=Member()
    duration=Member()
    plotmin=Member()
    plotmax=Member()
    
    def __init__(self,name,experiment,description='',digitalout=None,waveforms=None):
        super(NumpyWaveform,self).__init__(name,experiment,description)
        
        self.digitalout=digitalout
        self.waveforms=waveforms
        self.channelList=numpy.zeros(0,dtype=numpy.uint8)
        self.transitions=NumpyTransitions(self.experiment)
        self.sequence=NumpySequence(self.experiment)
        self.plotmin=-1
        self.plotmax=-1
        self.isEmpty=True
        self.properties+=['isEmpty','transitions','sequence','plotmin','plotmax','channelList']
        self.doNotSendToHardware+=['plotmin','plotmax']
        
        self.figure1=Figure(figsize=(5,5))
        self.figure2=Figure(figsize=(5,5))
        self.backFigure=self.figure2
        self.figure=self.figure1
    
    def copy(self):
        new=NumpyWaveform(self.name+'_copy',self.experiment,self.description,self.digitalout,self.waveforms)
        new.channelList=self.channelList.copy()
        new.transitions=self.transitions.copy()
        new.sequence=self.sequence.copy()
        new.plotmin=self.plotmin
        new.plotmax=self.plotmax
        new.evaluate()
        return new
    
    def fromXML(self, xmlNode):
        super(NumpyWaveform, self).fromXML(xmlNode)
        self.updateFigure()
        return self
    
    def fromHDF5(self, hdf):
        super(NumpyWaveform, self).fromHDF5(hdf)

        if len(self.channelList) < (numpy.shape(self.sequence.array)[1]):
            self.channelList = numpy.arange(self.digitalout.numChannels, dtype=numpy.uint8)
        self.updateFigure()
        return self
    
    def addTransition(self, index):
        self.transitions.add(index)
        self.sequence.addRow(index)
        self.evaluate()
    
    def removeTransition(self, index):
        self.transitions.remove(index)
        self.sequence.removeRow(index)
        self.evaluate()
    
    def addChannel(self, index):
        # insert the index number as the value at that position
        self.channelList = numpy.insert(self.channelList, index, index, axis=0)
        self.sequence.addColumn(index)
        self.evaluate()
    
    def removeChannel(self,index):
        self.channelList=numpy.delete(self.channelList,index,axis=0)
        self.sequence.removeColumn(index)
        self.evaluate()
    
    def format(self):
        """Create timeList, a 1D array of transition times, and stateList a 2D array of output values."""
        if len(self.transitions.array)==0:
            self.isEmpty=True
            self.timeList=numpy.zeros(0,dtype=numpy.uint64)
            self.stateList=numpy.zeros((0,len(self.digitalout.channels.array)),dtype=numpy.uint8)
            self.duration=numpy.zeros(0,dtype=numpy.uint64)
        else:
            self.isEmpty=False
            
            #create arrays
            timeList=self.transitions.array['value']
            stateList=self.sequence.array['value']
            
            #convert to integral samples
            #TODO: round to int, instead of floor to int
            temp=numpy.empty_like(timeList, dtype=numpy.uint64)
            timeList=numpy.rint(timeList*self.digitalout.clockRate.value*self.digitalout.units.value,out=temp)
            #timeList=(timeList*self.digitalout.clockRate.value*self.digitalout.units.value).astype(numpy.uint64)
            
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
            #for each channel
            for i in range(stateList.shape[1]):
                if stateList[0,i]==5:
                    stateList[0,i]=0
            #set other 5's to the prior state
            #for each time after 1st
            for i in range(1,len(timeList)):
                #for each channel
                for j in range(stateList.shape[1]):
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
            
            #add in zeros to all the channels that are not specified
            fullStateList=numpy.zeros((len(timeList),len(self.digitalout.channels.array)),dtype=numpy.uint8)
            #go through each column of stateList, and put it in the right slot, according to channelList
            for i in range(len(self.channelList)):
                #but only if that channel is active
                if self.digitalout.channels.array[self.channelList[i]]['value']:
                    fullStateList[:,self.channelList[i]]=stateList[:,i]
            
            # find the duration of each segment
            self.duration=timeList[1:]-timeList[:-1]
            self.duration=numpy.append(self.duration,numpy.array(1,dtype=numpy.uint64)) #add in a 1 sample duration at end for last transition
            
            #update the exposed variables
            self.timeList=timeList
            self.stateList=fullStateList
    
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
    
    def drawMPL(self):
        
        #draw on the inactive figure
        fig=self.backFigure
        
        #clear figure
        fig.clf()
        
        if not self.isEmpty:
            
            stateList = self.stateList
            #include final sample, and convert from samples to time
            timeList = numpy.append(self.timeList,
                                    numpy.array(self.timeList[-1]+1,
                                    dtype=numpy.uint64)).astype(numpy.float64)/(self.digitalout.clockRate.value*self.digitalout.units.value)
            duration = self.duration.astype(numpy.float64)/(self.digitalout.clockRate.value*self.digitalout.units.value)
            
            #get plot info
            numTransitions,numChannels = numpy.shape(stateList)
            
            #create axis
            ax = fig.add_subplot(111)
            ax.set_ylim(0, numChannels)
            ax.set_xlabel('time ['+self.digitalout.units.function+']')
            
            #create dummy lines for legend
            ax.plot((), (),  linewidth=5, alpha=0.5, color='white', label='off 0')
            ax.plot((), (), linewidth=5, alpha=0.5, color='black', label='on 1')
            #ax.plot((),(),linewidth=5,alpha=0.5,color='grey',label='unresolved')
            #ax.plot((),(),linewidth=5,alpha=0.5,color='red',label='invalid')
            ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.11), fancybox=True, ncol=2)
            
            #set up plot ticks
            ax.set_xticks(timeList)
            ax.set_xticklabels(map(lambda x: str.format('{:.6g}',x),timeList))
            
            #make horizontal grid lines
            ax.grid(True)
            
            #set plot limits
            if self.plotmin==-1:
                plotmin=timeList[0]
            else:
                plotmin=self.plotmin
            if self.plotmax==-1:
                plotmax=timeList[-1]
            else:
                plotmax=self.plotmax
            if plotmin==plotmax:
                #avoid divide by zeros
                plotmax+=1
            ax.set_xlim(plotmin, plotmax)
            
            #create a timeList on the scale 0 to 1
            relativeTimeList=(timeList-plotmin)/(plotmax-plotmin)
            relativeDuration=duration/(plotmax-plotmin)
            
            #Make a broken horizontal bar plot, i.e. one with gaps
            for i in xrange(numChannels):
                #reverse plot order of channels
                yhigh=numChannels-1-i+.9
                ylow=numChannels-1-i+.1
                for j in xrange(numTransitions):
                    if stateList[j,i]==1:
                        ax.axhspan(ylow,yhigh, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='black',alpha=0.5)
                    elif stateList[j,i]==5:
                        ax.axhspan(ylow,yhigh, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='grey',alpha=0.5)
                    elif stateList[j,i]>0:
                        ax.axhspan(ylow,yhigh, relativeTimeList[j],relativeTimeList[j]+relativeDuration[j], color='red',alpha=0.5)
                    #if value is zero, plot nothing

            #make vertical tick labels on the bottom
            for label in ax.xaxis.get_ticklabels():
                label.set_rotation(90)
            
            #setup y-axis ticks
            ax.set_yticks(numpy.arange(numChannels)+0.5)
            yticklabels=[x+(' : ' if x else ' ')+str(i) for i,x in enumerate(self.digitalout.channels.array['description'])]
            yticklabels.reverse() #reverse plot order of channels
            ax.set_yticklabels(yticklabels)
            
            #make sure the tick labels have room
            fig.subplots_adjust(left=.2,right=.95,bottom=.2)
    
    def swapFigures(self):
        temp = self.backFigure
        self.backFigure = self.figure
        self.figure = temp
    
    def updateFigure(self):
        """This function redraws the broken bar chart display of the waveform sequences."""

        if self.experiment.allow_evaluation:
            self.format()  # update processed sequence

            #Make the matplotlib plot
            self.drawMPL()

            try:
                deferred_call(self.swapFigures)
            except RuntimeError:  # application not started yet
                self.swapFigures()
    
    def remove(self):
        if self.waveforms is not None:
            self.waveforms.remove(self)  # remove ourselves from the master list, becoming subject to garbage collection
    
    def evaluate(self):
        if self.experiment.allow_evaluation:
            super(NumpyWaveform, self).evaluate()
            self.updateFigure()
    
    def toHardware(self):
            return ('<waveform>'+
                '<name>'+self.name+'</name>'+
                '<transitions>'+' '.join([str(time) for time in self.timeList])+'</transitions>'+
                '<states>'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.stateList])+'</states>\n'+
                '</waveform>\n')
