'''DDS.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the Direct Digital Synthesis frequency generators.  These are currently controlled
from LabView, via USB.
'''
from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

from atom.api import Bool, Int, Str, Typed, Member, List, observe, Atom
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument

class DDS_gui(Atom):
    deviceList=Member()
    boxDescriptionList=Member()

class DDS(Instrument):
    enable=Typed(BoolProp)
    boxes=Typed(ListProp)
    version=Member()
    communicator=Member() #holds the reference to the thing that sends DDS commands, usually the LabView object
    #deviceListStr=Str()
    deviceList=Member()
    boxDescriptionList=Member()
    
    def __init__(self,experiment,communicator):
        super(DDS,self).__init__('DDS',experiment)
        self.communicator=communicator
        self.version='2014.01.22'
        self.enable=BoolProp('enable',self.experiment,'enable DDS output','False')
        self.boxes=ListProp('boxes',experiment,listElementType=DDSbox,listElementName='box',listElementKwargs={'DDS':self})
        #self.addBox() #TODO:don't add this initial box, but if we don't then the comboBox doesn't update for some reason
        #self.deviceList=self.deviceListStr.split('\n')
        self.deviceList=[]
        self.boxDescriptionList=[]
        self.properties+=['version','enable','boxes','deviceList','boxDescriptionList']
    
    def evaluate(self):
        super(DDS,self).evaluate()
        self.updateBoxDescriptionList()
        
    
    def addBox(self):
        newbox=DDSbox('box'+str(len(self.boxes)),self.experiment,description='newbox',DDS=self)
        self.boxes.append(newbox)
        return newbox
    
    def getDDSDeviceList(self):
        result=self.communicator.send('<getDDSDeviceList/>')
        deviceListStr=result['DDS/devices']
        deferred_call(setattr,self,'deviceList',deviceListStr.split('\n'))
    
    def updateBoxDescriptionList(self):
        #sets the descriptions shown in the combo box in the GUI
        try:
            deferred_call(setattr,self,'boxDescriptionList',[str(i)+' '+n.description for i,n in enumerate(self.boxes)])
        except RuntimeError:
            #the GUI is not yet active
            self.boxDescriptionList=[str(i)+' '+n.description for i,n in enumerate(self.boxes)]
    
    def initializeDDS(self):
        #send just the DDS settings, force initialization, and then set DDS settings
        result=self.communicator.send('<uninitializeDDS/>'+self.toHardware())
        print result
    
    def loadDDS(self):
        #send just the DDS settings, initialize if neccessary, and then set DDS settings
        result=self.communicator.send(self.toHardware())
        print result

class DDSbox(Prop):
    enable=Bool()
    deviceReference=Str()
    DIOport=Int()
    channels=Typed(ListProp)
    DDS=Member()
    
    def __init__(self,name,experiment,description='',DDS=None):
        self.DDS=DDS
        super(DDSbox,self).__init__(name,experiment,description)
        '''each box has exactly 4 channels'''
        self.channels=ListProp('channels',experiment,listProperty=[DDSchannel('channel'+str(i),self.experiment) for i in range(4)],listElementType=DDSchannel,listElementName='channel')
        self.properties+=['enable','deviceReference','DIOport','channels']
    
    @observe('description')
    def descriptionChanged(self,change):
        self.DDS.updateBoxDescriptionList()

class DDSchannel(Prop):
    power=Typed(BoolProp)
    refClockRate=Typed(IntProp)
    fullScaleOutputPower=Typed(FloatProp)
    RAMenable=Typed(BoolProp)
    RAMDestType=Typed(IntProp)
    RAMDefaultFrequency=Typed(FloatProp)
    RAMDefaultAmplitude=Typed(FloatProp)
    RAMDefaultPhase=Typed(FloatProp)
    profiles=Typed(ListProp)
    profileDescriptionList=Member()
    
    def __init__(self,name,experiment,description=''):
        super(DDSchannel,self).__init__(name,experiment,description)
        self.power=BoolProp('power',self.experiment,'enable RF output from this channel','False')
        self.refClockRate=IntProp('refClockRate',self.experiment,'[MHz]','1000')
        self.fullScaleOutputPower=FloatProp('fullScaleOutputPower',self.experiment,'[dBm]','0')
        self.RAMenable=BoolProp('RAMenable',self.experiment,'RAM enable','False')
        self.RAMDestType=IntProp('RAMDestType',self.experiment,'RAM Destination Type (integer code)','0')
        self.RAMDefaultFrequency=FloatProp('RAMDefaultFrequency',self.experiment,'[MHz]','0')
        self.RAMDefaultAmplitude=FloatProp('RAMDefaultAmplitude',self.experiment,'[dBm]','0')
        self.RAMDefaultPhase=FloatProp('RAMDefaultPhase',self.experiment,'[rad]','0')
        '''each channel has exactly 8 profiles'''
        self.profileDescriptionList=[]
        self.profiles=ListProp('profiles',self.experiment,listProperty=[DDSprofile('profile'+str(i),self.experiment,channel=self) for i in range(8)],listElementType=DDSprofile,listElementName='profile',listElementKwargs={'channel':self})
        self.properties+=['power','refClockRate','fullScaleOutputPower','RAMenable','RAMDestType','RAMDefaultFrequency',
            'RAMDefaultAmplitude','RAMDefaultPhase','profiles','profileDescriptionList']
    
    def evaluate(self):
        super(DDSchannel,self).evaluate()
        self.updateProfileDescriptionList()
    
    def updateProfileDescriptionList(self):
        if self.profiles is not None:
            #sets the descriptions shown in the combo box in the GUI
            try:
                deferred_call(setattr,self,'profileDescriptionList',['{} {}'.format(i,n.description) for i,n in enumerate(self.profiles)])
            except RuntimeError:
                #the GUI is not yet active
                self.profileDescriptionList=['{} {}'.format(i,n.description) for i,n in enumerate(self.profiles)]

class DDSprofile(Prop):
    frequency=Typed(FloatProp)
    amplitude=Typed(FloatProp)
    phase=Typed(FloatProp)
    RAMMode=Typed(StrProp)
    ZeroCrossing=Typed(BoolProp)
    NoDwellHigh=Typed(BoolProp)
    FunctionOrStatic=Typed(BoolProp)
    RAMFunction=Typed(StrProp)
    RAMInitialValue=Typed(FloatProp)
    RAMStepValue=Typed(FloatProp)
    RAMTimeStep=Typed(FloatProp)
    RAMNumSteps=Typed(IntProp)
    RAMStaticArray=Typed(ListProp)
    channel=Member()
    
    def __init__(self,name,experiment,description='',channel=None):
        self.channel=channel
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
    
    @observe('description')
    def descriptionChanged(self,change):
        self.channel.updateProfileDescriptionList()
