'''HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

#from cs_errors import PauseError
from traits.api import Bool, Instance
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
import matplotlib.pyplot as plt
import numpy, logging
logger = logging.getLogger(__name__)

#---- HSDIO properties ----
class ScriptTrigger(Prop):
    id=Instance(StrProp)
    source=Instance(StrProp)
    type=Instance(StrProp)
    edge=Instance(StrProp)
    level=Instance(StrProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(ScriptTrigger,self).__init__('trigger',experiment,description)
        self.id=StrProp('id',experiment,'','"ScriptTrigger0"')
        self.source=StrProp('source',experiment,'','"PFI0"')
        self.type=StrProp('type',experiment,'','"edge"')
        self.edge=StrProp('edge',experiment,'','"rising"')
        self.level=StrProp('level',experiment,'','"high"')
        self.properties+=['id','source','type','edge','level']
        
class Channel(Prop):
    active=Instance(BoolProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(Channel,self).__init__(name,experiment,description)
        self.active=BoolProp('active',experiment,'','True')
        self.properties+=['active']

class Channels(ListProp):    
    def __init__(self,experiment,HSDIO,description='A list of HSDIO channels'):
        super(Channels,self).__init__('channels',experiment,description,
            listProperty=[Channel(str(i),experiment,'') for i in xrange(HSDIO.numChannels)],
            listElementType=Channel)
        self.HSDIO=HSDIO
        
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
    def __init__(self,experiment,HSDIO):
        super(State,self).__init__('state',experiment,
            listProperty=[IntProp('channel'+str(i),experiment,'','5') for i in range(HSDIO.numChannels)],
            listElementType=IntProp)
        self.HSDIO=HSDIO
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[IntProp(str(i),self.experiment,'','5').fromXML(child) for i, child in enumerate(xmlNode)]
        return self

class Transition(Prop):
    time=Instance(FloatProp) #when does this transition happen
    
    def __init__(self,experiment,HSDIO,description=''):
        super(Transition,self).__init__('transition',experiment,description)
        self.HSDIO=HSDIO
        self.time=FloatProp('time',self.experiment,'when this transition happens','0')
        self.state=State(self.experiment,self.HSDIO)
        self.properties+=['time','state']

class Sequence(ListProp):
    def __init__(self,experiment,HSDIO):
        super(Sequence,self).__init__('sequence',experiment,listElementType=Transition)
        self.HSDIO=HSDIO
        
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Transition(self.experiment,self.HSDIO).fromXML(child) for child in xmlNode]
        return self


class Waveform(Prop):
    figure=Instance(plt.Figure)
    refresh=Bool
    
    def __init__(self,name,experiment,HSDIO,description='',waveforms=None):
        super(Waveform,self).__init__(name,experiment,description)
        self.HSDIO=HSDIO
        self.waveforms=waveforms
        self.sequence=Sequence(self.experiment,self.HSDIO) #start with no transitions
        self.isEmpty=True
        self.properties+=['isEmpty','sequence']
        
        #setup the figure that will be used for plotting sequences
        fig, ax = plt.subplots()
        ax.set_ylim(0,self.HSDIO.numChannels)
        ax.set_xlabel('samples')
        #create dummy lines for legend
        ax.plot((),(),color='white',label='off 0')
        ax.plot((),(),color='black',label='on 1')
        ax.plot((),(),color='grey',label='unresolved 5')
        ax.plot((),(),color='red',label='invalid')
        ax.legend(loc='upper center',bbox_to_anchor=(0.5, 1.1), fancybox=True, ncol=4)
        
        self.figure=fig
        self.ax=ax
        
        self.updateFigure()
    
    def fromXML(self,xmlNode):
        super(Waveform,self).fromXML(xmlNode)
        self.updateFigure()
        return self
    
    def addTransition(self):
        newTransition=Transition(self.experiment,self.HSDIO)
        self.sequence.append(newTransition)
        self.updateFigure()
        return newTransition
        
    def toHSDIOformat(self):
        if len(self.sequence)==0:
            self.isEmpty=True
            self.timeList=numpy.zeros(0,dtype=int)
            self.stateList=numpy.zeros((0,self.HSDIO.numChannels),dtype='uint8')
            self.duration=numpy.zeros(0,dtype=int)
        else:
            self.isEmpty=False
            timeList=numpy.array([i.time.value for i in self.sequence])
            stateList=numpy.array([[channel.value for channel in transition.state] for transition in self.sequence],dtype='uint8') #channel here refers to an IntProp, not to a Channel
            order=timeList.argsort()
            self.timeList=numpy.array(timeList[order]*self.waveforms.HSDIO.clockRate.value,dtype=int) #convert to samples
            self.stateList=stateList[order]
            
            #if the waveform doesn't start with time 0, add it, and add 5's to the beginning of statelist
            #LabView will modify the waveform in unpredictable ways if it doesn't start with time 0
            if self.timeList[0]!=0:
                self.timeList=numpy.insert(self.timeList,0,0,axis=0)
                self.stateList=numpy.insert(self.stateList,0,5,axis=0)
            
            self.duration=[self.timeList[i+1]-self.timeList[i] for i in xrange(len(self.timeList)-1)]
            self.duration.append(1) #add in a 1 sample duration at end for last transition

    def colorMap(val):
        '''The color map for plotting HSDIO sequence bar charts.  Red indicates an invalid value.'''
        if val==0:
            return 'white'
        elif val==1:
            return 'black'
        elif val==5:
            return 'grey'
        else:
            return 'red'

    #create a version of the colorMap function that can be passed arrays
    vColorMap=numpy.vectorize(colorMap) 

    def updateFigure(self):
        '''This function redraws the broken bar chart display of the waveform sequences.'''
        self.toHSDIOformat() #update processed sequence

        self.ax.collections=[] #clear old plots

        if not self.isEmpty:
            #figure out how to resolve '5' unchanged samples
            displayArray=self.stateList.copy()
            for i in xrange(self.HSDIO.numChannels): #for each channel
                for j in range(1,len(self.timeList)): #go through the sequence, but not the first item
                    if displayArray[j,i]==5:
                        displayArray[j,i]=displayArray[j-1,i] #change the '5' to be whatever was before it                    
            
            #Make a broken horizontal bar plot, i.e. one with gaps
            data=zip(self.timeList,self.duration)
            
            for i in xrange(self.HSDIO.numChannels):
                facecolors=self.vColorMap(displayArray[:,i]) #convert the digital values to colors
                self.ax.broken_barh(data,(i,0.8),facecolors=facecolors,linewidth=0)
            self.ax.set_xlim(self.timeList[0],self.timeList[-1]+1)
            tickList=self.timeList.copy()
            tickList=numpy.insert(self.timeList,-1,self.timeList[-1]+1) #add one sample to the end
            self.ax.set_xticks(tickList)
            self.ax.set_yticks(numpy.arange(self.HSDIO.numChannels)+0.4)
            self.ax.set_yticklabels([str(i)+': '+self.experiment.LabView.HSDIO.channels[i].description for i in range(self.HSDIO.numChannels)])
            
        #toggle the refresh boolean to update the screen
        try:
            self.refresh=not self.refresh
        except Exception as e:
            logger.warning('Exception while trying to refresh waveform plot.  You probably updated the enaml package recently.'+
            'You must add a function to QtMPLCanvas in\n'+
            'C:\Users\Saffmanlab\AppData\Local\Enthought\Canopy\User\Lib\site-packages\enaml\qt\qt_mpl_canvas.py'+'\n'+
            '    def on_action_set_refresh(self, content):'+'\n'+
            '        self.refresh_mpl_widget()')
    
    def remove(self):
        index=self.waveforms.waveforms.remove(self) #remove ourselves from the master list, becoming subject to garbage collection
    
    def evaluate(self):
        super(Waveform,self).evaluate()
        self.updateFigure()
    
    def toHardware(self):
            self.toHSDIOformat()
            return ('<waveform>'+
                '<name>'+self.name+'</name>'+
                '<transitions>'+' '.join([str(time) for time in self.timeList])+'</transitions>'+
                '<states>\n'+'\n'.join([' '.join([str(sample) for sample in state]) for state in self.stateList])+'\n</states>\n'+
                '</waveform>\n')
                
class Waveforms(ListProp):
    def __init__(self,experiment,HSDIO):
        super(Waveforms,self).__init__('waveforms',experiment,description='Holds all the HSDIO waveforms',listElementType=Waveform)
        self.HSDIO=HSDIO
        self.add()
        #self.refresh()
        
    
    def getNextAvailableName(self):
        #figure out unique name for a new waveform
        count=int(0)
        names=[i.name for i in self.listProperty]
        while True:
            name='wfm'+str(count)
            if not name in names:
                return name
            count+=1

    def add(self):
        name=self.getNextAvailableName()
        waveform=Waveform(name,self.experiment,self.HSDIO,waveforms=self)
        self.listProperty.append(waveform)
        return waveform
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Waveform(self.getNextAvailableName(),self.experiment,self.HSDIO,waveforms=self).fromXML(child) for child in xmlNode]
        self.refresh()
        return self
    
    def refresh(self):
        if hasattr(self,'refreshButton'): #prevents trying to do this before GUI is active
            self.refreshButton.clicked()  #refresh the GUI

#---- HSDIO instrument ----

class HSDIO(Instrument):
    enable=Instance(BoolProp)
    script=Instance(StrProp)
    resourceName=Instance(StrProp)
    clockRate=Instance(FloatProp)
    units=Instance(FloatProp)
    hardwareAlignmentQuantum=Instance(IntProp)
    waveforms=Instance(Waveforms)
    channels=Instance(Channels)
    triggers=Instance(ListProp)

    def __init__(self,experiment):
        super(HSDIO,self).__init__('HSDIO',experiment)
        self.version='2013.10.19'
        self.numChannels=32
        self.enable=BoolProp('enable',experiment,'enable HSDIO output','False')
        self.script=StrProp('script',experiment,'HSDIO script that says what waveforms to generate',"'script script1\\n  generate waveform1\\n  idle\\nend script'")
        self.resourceName=StrProp('resourceName',experiment,'the hardware location of the HSDIO card',"'Dev1'")
        self.clockRate=FloatProp('clockRate',experiment,'samples/channel/sec','1000')
        self.units=FloatProp('units',experiment,'multiplier for HSDIO timing values (milli=.001)','1')
        self.hardwareAlignmentQuantum=IntProp('hardwareAlignmentQuantum',experiment,'(PXI=1,SquareCell=2)','1')
        self.waveforms=Waveforms(experiment,self)
        self.channels=Channels(experiment,self)
        self.triggers=ListProp('triggers',self.experiment,listElementType=ScriptTrigger,listElementName='trigger')
        self.properties+=['version','enable','script','resourceName','clockRate','units','hardwareAlignmentQuantum','waveforms','triggers','channels']
        
    def initialize(self):
        self.isInitialized=True
        
    # def addWaveform(self):
        # return self.waveforms.add()
    
    def addTrigger(self):
        new=ScriptTrigger('trigger'+str(len(self.triggers)),self.experiment)
        self.triggers.append(new)
        return new