'''DAQmxPulse.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2013-10-19

This file holds everything to model a National Instruments DAQmx pulse output.  It communicated to LabView via the higher up LabView class.
'''

#from cs_errors import PauseError
from cs_instruments import Instrument
import logging
logger = logging.getLogger(__name__)



#from cs_errors import PauseError
from atom.api import Bool, Typed, Member
#from enthought.chaco.api import ArrayPlotData, Plot #for chaco plot
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
import matplotlib.pyplot as plt
import numpy, logging
logger = logging.getLogger(__name__)
from digital_waveform import Waveform, Channels

#---- DAQmx properties ----


class StartTrigger(Prop):
    waitForStartTrigger=Typed(BoolProp)
    source=Typed(StrProp)
    edge=Typed(StrProp)
    
    def __init__(self,experiment):
        super(StartTrigger,self).__init__('startTrigger',experiment)
        self.waitForStartTrigger=BoolProp('waitForStartTrigger',experiment,'wait for start trigger','False')
        self.source=StrProp('source',experiment,'start trigger source','"PFI0"')
        self.edge=StrProp('edge',experiment,'start trigger edge','"rising"')
        self.properties+=['waitForStartTrigger','source','edge']
        

#---- DAQmxPulse instrument ----

class DAQmxPulse(Instrument):
    enable=Typed(BoolProp)
    script=Typed(StrProp)
    resourceName=Typed(StrProp)
    clockRate=Typed(FloatProp)
    units=Typed(FloatProp)
    hardwareAlignmentQuantum=Typed(IntProp)
    waveform=Typed(Waveform)
    channels=Typed(Channels)
    triggers=Typed(ListProp)
    startTrigger=Typed(StartTrigger)
    version=Member()
    numChannels=Member()

    def __init__(self,experiment):
        super(DAQmxPulse,self).__init__('DAQmxPulse',experiment)
        self.version='2014.01.13'
        self.numChannels=32
        self.enable=BoolProp('enable',experiment,'enable output','False')
        self.resourceName=StrProp('resourceName',experiment,'the hardware location of the card',"'Dev1'")
        self.clockRate=FloatProp('clockRate',experiment,'samples/channel/sec','1000')
        self.units=FloatProp('units',experiment,'multiplier for timing values (milli=.001)','1')
        self.waveform=Waveform('waveform',experiment,self)
        self.channels=Channels(experiment,self)
        self.startTrigger=StartTrigger(experiment)
        self.properties+=['version','enable','resourceName','clockRate','units','waveform','channels','startTrigger']
        
    def initialize(self):
        self.isInitialized=True
        
    # def addWaveform(self):
        # return self.waveforms.add()
    
    def addTrigger(self):
        new=ScriptTrigger('trigger'+str(len(self.triggers)),self.experiment)
        self.triggers.append(new)
        return new