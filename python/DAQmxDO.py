'''DAQmxDO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2014-03-25

This file holds everything to model a National Instruments DAQmx pulse output.  It communicated to LabView via the higher up LabView class.
'''

from cs_errors import setupLog #,PauseError
logger=setupLog(__name__)

from cs_instruments import Instrument

from atom.api import Typed, Member
#from enthought.chaco.api import ArrayPlotData, Plot #for chaco plot
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp, EnumProp
from digital_waveform import Waveform, NumpyChannels
import numpy

#---- DAQmxDO properties ----

class StartTrigger(Prop):
    waitForStartTrigger=Typed(BoolProp)
    source=Typed(StrProp)
    edge=Typed(EnumProp)
    
    def __init__(self,experiment):
        super(StartTrigger,self).__init__('startTrigger',experiment)
        self.waitForStartTrigger=BoolProp('waitForStartTrigger',experiment,'wait for start trigger','False')
        self.source=StrProp('source',experiment,'start trigger source','"PFI0"')
        self.edge=EnumProp('edge',experiment,'start trigger edge','"rising"',["rising","falling"])
        self.properties+=['waitForStartTrigger','source','edge']

#---- DAQmxDO instrument ----

class DAQmxDO(Instrument):
    enable=Typed(BoolProp)
    script=Typed(StrProp)
    resourceName=Typed(StrProp)
    clockRate=Typed(FloatProp)
    units=Typed(FloatProp)
    hardwareAlignmentQuantum=Typed(IntProp)
    waveform=Typed(Waveform)
    #channels=Typed(Channels)
    channels=Member()
    triggers=Typed(ListProp)
    startTrigger=Typed(StartTrigger)
    version=Member()
    numChannels=Member()

    def __init__(self,experiment):
        super(DAQmxDO,self).__init__('DAQmxDO',experiment)
        self.version='2014.03.25'
        self.numChannels=32
        self.enable=BoolProp('enable',experiment,'enable output','False')
        self.resourceName=StrProp('resourceName',experiment,'the hardware location of the card',"'Dev1'")
        self.clockRate=FloatProp('clockRate',experiment,'samples/channel/sec','1000')
        self.units=FloatProp('units',experiment,'multiplier for timing values (milli=.001)','1')
        self.waveform=Waveform('waveform',experiment,self)
        #self.channels=Channels(experiment,self)
        self.channels=NumpyChannels(experiment)
        self.startTrigger=StartTrigger(experiment)
        self.properties+=['version','enable','resourceName','clockRate','units','waveform','channels','startTrigger']
        self.doNotSendToHardware+=['units','waveform','channels'] #waveform is handled specially in toHardware() and channels needs to be setup differently
        
    def initialize(self):
        self.isInitialized=True
        
    def toHardware(self):
        #create a zeros array of size (numTransitions,len(channels.array))
        output=numpy.zeros((self.waveform.array['states'].shape[1],len(self.channels.array)),dtype=bool)
        #for each line in the waveform
        for i in self.waveform.array:
            #if the channel is active
            if self.channels.array[i['channel']]['value']:
                #add it to the output array
                x=i['states']
                if x[0]==5:
                    x[0]=0
                for i,n in enumerate(x[1:]):
                    if n==5:
                        if i==0:
                            x[i]=0
                        else:
                            x[i]=x[i-1]
                
            #else leave it as zeros
            
    
        #make sure to include the usual properties
        return super(DAQmxDO,self).toHardware()
        