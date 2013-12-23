'''DDS.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the Direct Digital Synthesis frequency generators.  These are currently controlled
from LabView, via USB.
'''

#from cs_errors import PauseError
from traits.api import Bool, Int, Str, Instance
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
import logging
logger = logging.getLogger(__name__)

class DDS(Instrument):
    enable=Instance(BoolProp)
    boxes=Instance(ListProp)
    
    def __init__(self,experiment):
        super(DDS,self).__init__('DDS',experiment)
        self.version='2013.10.20'
        self.enable=BoolProp('enable',self.experiment,'enable DDS output','False')
        self.boxes=ListProp('boxes',experiment,listElementType=DDSbox,listElementName='box')
        self.addBox() #TODO:don't add this initial box, but if we don't then the comboBox doesn't update for some reason
        self.properties+=['version','enable','boxes']
    
    def addBox(self):
        newbox=DDSbox('box'+str(len(self.boxes)),self.experiment)
        self.boxes.append(newbox)
        return newbox

class DDSbox(Prop):
    enable=Bool
    deviceReference=Str
    DIOport=Int
    channels=Instance(ListProp)

    def __init__(self,name,experiment,description='',kwargs={}):
        super(DDSbox,self).__init__(name,experiment,description)
        '''each box has exactly 4 channels'''
        self.channels=ListProp('channels',experiment,listProperty=[DDSchannel('channel'+str(i),self.experiment) for i in range(4)],listElementType=DDSchannel,listElementName='channel')
        self.properties+=['enable','deviceReference','DIOport','channels']

class DDSchannel(Prop):
    power=Instance(BoolProp)
    refClockRate=Instance(IntProp)
    fullScaleOutputPower=Instance(FloatProp)
    RAMenable=Instance(BoolProp)
    RAMDestType=Instance(IntProp)
    RAMDefaultFrequency=Instance(FloatProp)
    profiles=Instance(ListProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(DDSchannel,self).__init__(name,experiment,description)
        self.power=BoolProp('power',self.experiment,'enable RF output from this channel','False')
        self.refClockRate=IntProp('refClockRate',self.experiment,'[kHz]','0')
        self.fullScaleOutputPower=FloatProp('fullScaleOutputPower',self.experiment,'[dBm]','0')
        self.RAMenable=BoolProp('RAMenable',self.experiment,'RAM enable','False')
        self.RAMDestType=IntProp('RAMDestType',self.experiment,'RAM Destination Type (integer code)','0')
        self.RAMDefaultFrequency=FloatProp('RAMDefaultFrequency',self.experiment,'[MHz]','0')
        self.RAMDefaultAmplitude=FloatProp('RAMDefaultAmplitude',self.experiment,'[dBm]','0')
        self.RAMDefaultPhase=FloatProp('RAMDefaultPhase',self.experiment,'[rad]','0')
        '''each channel has exactly 8 profiles'''
        self.profiles=ListProp('profiles',self.experiment,listProperty=[DDSprofile('profile'+str(i),self.experiment) for i in range(8)],listElementType=DDSprofile,listElementName='profile')
        self.properties+=['power','refClockRate','fullScaleOutputPower','RAMenable','RAMDestType','RAMDefaultFrequency',
            'RAMDefaultAmplitude','RAMDefaultPhase','profiles']

class DDSprofile(Prop):
    frequency=Instance(FloatProp)
    amplitude=Instance(FloatProp)
    phase=Instance(FloatProp)
    RAMMode=Instance(StrProp)
    ZeroCrossing=Instance(BoolProp)
    NoDwellHigh=Instance(BoolProp)
    FunctionOrStatic=Instance(BoolProp)
    RAMFunction=Instance(StrProp)
    RAMInitialValue=Instance(FloatProp)
    RAMStepValue=Instance(FloatProp)
    RAMTimeStep=Instance(FloatProp)
    RAMNumSteps=Instance(IntProp)
    RAMStaticArray=Instance(ListProp)
    
    def __init__(self,name,experiment,description='',kwargs={}):
        super(DDSprofile,self).__init__(name,experiment,description)
        self.frequency=FloatProp('frequency',self.experiment,'[MHz]','0')
        self.amplitude=FloatProp('amplitude',self.experiment,'[dBm]','0')
        self.phase=FloatProp('phase',self.experiment,'[rad]','0')
        self.RAMMode=StrProp('RAMMode',self.experiment,'','"Direct Switch"')
        self.ZeroCrossing=BoolProp('ZeroCrossing',self.experiment,'','False')
        self.NoDwellHigh=BoolProp('NoDwellHigh',self.experiment,'','False')
        self.FunctionOrStatic=BoolProp('FunctionOrStatic',self.experiment,'','False')
        self.RAMFunction=StrProp('RAMFunction',self.experiment,'','""')
        self.RAMInitialValue=FloatProp('RAMInitialValue',self.experiment,'','0')
        self.RAMStepValue=FloatProp('RAMStepValue',self.experiment,'','0')
        self.RAMTimeStep=FloatProp('RAMTimeStep',self.experiment,'','0')
        self.RAMNumSteps=IntProp('RAMNumSteps',self.experiment,'','0')
        self.RAMStaticArray=ListProp('RAMStaticArray',self.experiment,listElementType=IntProp,listElementName='int')
        self.properties+=['frequency','amplitude','phase','RAMMode','ZeroCrossing','NoDwellHigh',
            'FunctionOrStatic','RAMFunction','RAMInitialValue','RAMStepValue','RAMTimeStep','RAMNumSteps','RAMStaticArray']