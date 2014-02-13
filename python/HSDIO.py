'''HSDIO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

from cs_errors import PauseError
from atom.api import Bool, Typed, Str, Int, Member
#from enthought.chaco.api import ArrayPlotData, Plot #for chaco plot
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
import matplotlib.pyplot as plt
import numpy, logging
logger = logging.getLogger(__name__)

from digital_waveform import Waveform, Channels
#import digital_waveform #my helper class for making Chaco plots of waveforms

#---- HSDIO properties ----
class ScriptTrigger(Prop):
    id=Typed(StrProp)
    source=Typed(StrProp)
    type=Typed(StrProp)
    edge=Typed(StrProp)
    level=Typed(StrProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(ScriptTrigger,self).__init__('trigger',experiment,description)
        self.id=StrProp('id',experiment,'','"ScriptTrigger0"')
        self.source=StrProp('source',experiment,'','"PFI0"')
        self.type=StrProp('type',experiment,'','"edge"')
        self.edge=StrProp('edge',experiment,'','"rising"')
        self.level=StrProp('level',experiment,'','"high"')
        self.properties+=['id','source','type','edge','level']

class Waveforms(ListProp):
    digitalout=Member()
    refreshButton=Member()

    def __init__(self,experiment,digitalout):
        super(Waveforms,self).__init__('waveforms',experiment,description='Holds all the digitalout waveforms',listElementType=Waveform)
        self.digitalout=digitalout
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
        waveform=Waveform(name,self.experiment,self.digitalout,waveforms=self)
        self.listProperty.append(waveform)
        return waveform
    
    def fromXML(self,xmlNode):
        while self.listProperty: #go until the list is empty
            self.listProperty.pop()
        self.listProperty+=[Waveform(self.getNextAvailableName(),self.experiment,self.digitalout,waveforms=self).fromXML(child) for child in xmlNode]
        self.refresh()
        return self
    
    def refresh(self):
        if hasattr(self,'refreshButton') and (self.refreshButton is not None): #prevents trying to do this before GUI is active
            self.refreshButton.clicked()  #refresh the GUI

class StartTrigger(Prop):
    waitForStartTrigger=Typed(BoolProp)
    source=Typed(StrProp)
    edge=Typed(StrProp)
    
    def __init__(self,experiment):
        super(StartTrigger,self).__init__('startTrigger',experiment)
        self.waitForStartTrigger=BoolProp('waitForStartTrigger',experiment,'HSDIO wait for start trigger','False')
        self.source=StrProp('source',experiment,'start trigger source','"PFI0"')
        self.edge=StrProp('edge',experiment,'start trigger edge','"rising"')
        self.properties+=['waitForStartTrigger','source','edge']

class Script(StrProp):
    
    #override to accommodate compressedGenerate
    def toHardware(self):
        #need to pass in list of waveforms in HSDIO.waveforms
        
        waveforms={i.name:i for i in HSDIO.waveforms} #build dictionary of waveforms keyed on waveform name
        for row in self.script.value.split('\n'):
            words=row.strip().split()
            if len(words)>1:
                command=words[0].lower()
                waveformName=words[1]
                if command='generate':
                    if waveformName not in waveformNames:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row,words[1]))
                        raise PauseError
                    elif waveformName not in HSDIO.waveformsToLoad:
                        #load it
                        HSDIO.waveformsToLoad+=[waveformName]
                        #add waveform to those to be transferred to LabView
                        pass
                elif command=='compressedgenerate':
                    newString=''
                    if waveformName not in waveformNames:
                        logger.warning('HSDIO script says: {}, but waveform {} does not exist.'.format(row,words[1]))
                        raise PauseError
                    for state,duration in zip(waveform.stateList,waveform.duration): #iterates over first index, which is time points
                        singleSampleWaveformName='w'+hex(int(''.join([str(i) for i in state])))[2:] #make a hexadecimal name for the waveform.  the [2:] drops the leading 0x on the hexadecimal
                        newString+='generate '+singleSampleWaveformName+'\n'
                        if duration > HSDIO.hardwareAlignmentQuantum.value:
                            if (duration-HSDIO.hardwareAlignmentQuantum.value)%HSDIO.hardwareAlignmentQuantum.value!=0:
                               waitTime=(int((duration-HSDIO.hardwareAlignmentQuantum.value)/HSDIO.hardwareAlignmentQuantum.value)+1)*HSDIO.hardwareAlignmentQuantum.value
                            else:
                                waitTime=int(duration-HSDIO.hardwareAlignmentQuantum.value)
                            newString+=int(waitTime/536870912)*'wait 536870912\n' #the HSDIO card cannot handle a wait value longer than this, so we repeat it as many times as necessary
                            newString+='wait '+str(waitTime%536870912)+'\n'
                        if not singleSampleWaveformName in HSDIO.waveformsToLoad:
                            #create waveformName (sample times hardwareAlignmentQuantum) and then add it to waveformsToLoad


        try:
            valueStr=str(self.value)
        except Exception as e:
            logger.warning('Exception in str(self.value) in EvalProp.toHardware() in '+self.name+' .\n'+str(e))
            raise PauseError
        return '<{}>{}</{}>\n'.format(self.name,valueStr,self.name)

#---- HSDIO instrument ----

class HSDIO(Instrument):
    enable=Typed(BoolProp)
    script=Typed(StrProp)
    resourceName=Typed(StrProp)
    clockRate=Typed(FloatProp)
    units=Typed(FloatProp)
    hardwareAlignmentQuantum=Typed(IntProp)
    waveforms=Typed(Waveforms)
    channels=Typed(Channels)
    triggers=Typed(ListProp)
    startTrigger=Typed(StartTrigger)
    version=Str()
    numChannels=Int()
    
    def __init__(self,experiment):
        super(HSDIO,self).__init__('HSDIO',experiment)
        self.version='2014.01.22'
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
        self.startTrigger=StartTrigger(experiment)
        self.properties+=['version','enable','script','resourceName','clockRate','units','hardwareAlignmentQuantum','waveforms','triggers','channels','startTrigger']
    
    def initialize(self):
        self.isInitialized=True
    
    def addTrigger(self):
        new=ScriptTrigger('trigger'+str(len(self.triggers)),self.experiment)
        self.triggers.append(new)
        return new
