"""
DAQmxDO.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2014-03-25

This file holds everything to model a National Instruments DAQmx pulse output.  It communicated to LabView via the higher up LabView class.
"""

from cs_errors import setupLog  # ,PauseError
logger = setupLog(__name__)

from cs_instruments import Instrument

from atom.api import Typed, Member
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, EnumProp
from digital_waveform import NumpyChannels, NumpyWaveform

#---- DAQmxDO properties ----


class StartTrigger(Prop):
    waitForStartTrigger = Typed(BoolProp)
    source = Typed(StrProp)
    edge = Typed(EnumProp)
    
    def __init__(self, experiment):
        super(StartTrigger, self).__init__('startTrigger', experiment)
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, 'wait for start trigger', 'False')
        self.source = StrProp('source', experiment, 'start trigger source', '"PFI0"')
        self.edge = EnumProp('edge', experiment, 'start trigger edge', '"rising"', ["rising", "falling"])
        self.properties += ['waitForStartTrigger', 'source', 'edge']

#---- DAQmxDO instrument ----


class DAQmxDO(Instrument):
    version = '2014.03.25'
    enable = Typed(BoolProp)
    script = Typed(StrProp)
    resourceName = Typed(StrProp)
    clockRate = Typed(FloatProp)
    units = Typed(FloatProp)
    hardwareAlignmentQuantum = Typed(IntProp)
    waveform = Member()
    channels = Member()
    triggers = Member()
    startTrigger = Member()
    numChannels = 8
    
    def __init__(self, experiment):
        super(DAQmxDO, self).__init__('DAQmxDO', experiment)
        self.enable = BoolProp('enable', experiment, 'enable output','False')
        self.resourceName = StrProp('resourceName', experiment, 'the hardware location of the card', "'Dev1'")
        self.clockRate = FloatProp('clockRate', experiment, 'samples/channel/sec', '1000')
        self.units = FloatProp('units', experiment, 'multiplier for timing values (milli=.001)', '1')
        self.channels = NumpyChannels(experiment, self)
        self.waveform = NumpyWaveform('waveform', experiment, digitalout=self)
        self.startTrigger = StartTrigger(experiment)
        self.properties += ['version', 'enable', 'resourceName', 'clockRate', 'units', 'channels', 'waveform', 'startTrigger']
        # the number of channels is defined by the resourceName (and the waveform which must agree), so
        # channels need not be send to hardware
        self.doNotSendToHardware += ['units', 'channels']
    
    def initialize(self):
        self.isInitialized = True
