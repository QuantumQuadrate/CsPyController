"""DDS.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-08
modified>=2013-10-08

This file holds everything needed to model the Direct Digital Synthesis frequency generators.  These are currently controlled
from LabView, via USB.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

import threading

from atom.api import Bool, Int, Float, Str, Typed, Member, List, observe, Atom
from enaml.application import deferred_call
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument

class DDS_gui(Atom):
    deviceList=Member()
    boxDescriptionList=Member()

class DDS(Instrument):
    version = '2014.07.16'
    boxes = Typed(ListProp)
    communicator = Member() #holds the reference to the thing that sends DDS commands, usually the LabView object
    #deviceListStr=Str()
    deviceList = Member()
    boxDescriptionList = Member()

    def __init__(self,experiment,communicator):
        super(DDS,self).__init__('DDS',experiment)
        self.communicator=communicator
        self.boxes=ListProp('boxes',experiment,listElementType=DDSbox,listElementName='box',listElementKwargs={'DDS':self})
        self.deviceList=[]
        self.boxDescriptionList=[]
        self.properties+=['version', 'boxes','deviceList','boxDescriptionList']
        self.doNotSendToHardware+=['deviceList','boxDescriptionList']

    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('DDS.evaluate()')
            super(DDS,self).evaluate()
            self.updateBoxDescriptionList()

    def getDDSDeviceListThread(self):
        thread = threading.Thread(target=self.getDDSDeviceList)
        thread.daemon = True
        thread.start()

    def getDDSDeviceList(self):
        print 'DDS: Requesting device list ...'
        result=self.communicator.send('<LabView><getDDSDeviceList/></LabView>')
        deviceListStr=result['DDS/devices']
        deferred_call(setattr,self,'deviceList',deviceListStr.split('\n'))
        print 'DDS: ... done.'
    
    def updateBoxDescriptionList(self):
        #sets the descriptions shown in the combo box in the GUI
        try:
            deferred_call(setattr,self,'boxDescriptionList',[str(i)+' '+n.description for i,n in enumerate(self.boxes)])
        except RuntimeError:
            #the GUI is not yet active
            self.boxDescriptionList=[str(i)+' '+n.description for i, n in enumerate(self.boxes)]

    def initializeDDSThread(self):
        thread = threading.Thread(target=self.initializeDDS)
        thread.daemon = True
        thread.start()

    def initializeDDS(self):
        #send just the DDS settings, force initialization, and then set DDS settings
        #This is not used as the instrument.initialize method at this time

        print 'DDS: Requesting initialize and load ...'
        result = self.communicator.send('<LabView><uninitializeDDS/>'+self.toHardware()+'</LabView>')
        self.isInitialized = True
        print 'DDS: ... done.'

    def loadDDSThread(self):
        thread = threading.Thread(target=self.loadDDS)
        thread.daemon = True
        thread.start()

    def loadDDS(self):
        #send just the DDS settings, initialize if neccessary, and then set DDS settings
        print 'DDS: Loading settings ...'
        result = self.communicator.send('<LabView>'+self.toHardware()+'</LabView>')
        self.isInitialized=True
        print 'DDS: ... done.'

class DDSbox(Prop):
    enable = Bool()
    deviceReference = Str()
    DIOport = Int()
    serialClockRate = Int()
    channels = Typed(ListProp)
    DDS = Member()
    
    def __init__(self, name, experiment, description='', DDS=None):
        self.DDS = DDS
        self.enable=False
        self.DIOport=0
        self.serialClockRate=1000
        super(DDSbox, self).__init__(name, experiment, description)
        '''each box has exactly 4 channels'''
        self.channels = ListProp('channels',experiment,listProperty=[DDSchannel('channel',self.experiment) for i in range(4)],listElementType=DDSchannel,listElementName='channel')
        self.properties += ['enable', 'deviceReference', 'DIOport', 'serialClockRate', 'channels']
    
    @observe('description')
    def descriptionChanged(self, change):
        self.DDS.updateBoxDescriptionList()


class DDSchannel(Prop):
    power = Typed(BoolProp)
    refClockRate = Typed(IntProp)
    fullScaleOutputPower = Typed(FloatProp)
    RAMenable = Typed(BoolProp)
    RAMDestType = Typed(IntProp)
    RAMDefaultFrequency = Typed(FloatProp)
    RAMDefaultAmplitude = Typed(FloatProp)
    RAMDefaultPhase = Typed(FloatProp)
    profiles = Typed(ListProp)
    profileDescriptionList = Member()
    
    def __init__(self, name, experiment, description=''):
        super(DDSchannel, self).__init__(name, experiment, description)
        self.power = BoolProp('power', self.experiment, 'enable RF output from this channel', 'False')
        self.refClockRate = IntProp('refClockRate', self.experiment, '[MHz]', '1000')
        self.fullScaleOutputPower = FloatProp('fullScaleOutputPower', self.experiment, '[dBm]', '0')
        self.RAMenable = BoolProp('RAMenable', self.experiment, 'RAM enable', 'False')
        self.RAMDestType = IntProp('RAMDestType', self.experiment, '0:Frequency,1:Phase,2:Amplitude,3:Polar', '0')
        self.RAMDefaultFrequency = FloatProp('RAMDefaultFrequency', self.experiment, '[MHz]', '0')
        self.RAMDefaultAmplitude = FloatProp('RAMDefaultAmplitude', self.experiment, '[dBm]', '0')
        self.RAMDefaultPhase = FloatProp('RAMDefaultPhase', self.experiment, '[rad]', '0')
        '''each channel has exactly 8 profiles'''
        self.profileDescriptionList = []
        self.profiles = ListProp('profiles', self.experiment, listProperty=[DDSprofile('profile', self.experiment, channel=self) for i in range(8)], listElementType=DDSprofile, listElementName='profile', listElementKwargs={'channel': self})
        self.properties += ['power', 'refClockRate', 'fullScaleOutputPower', 'RAMenable', 'RAMDestType', 'RAMDefaultFrequency',
            'RAMDefaultAmplitude', 'RAMDefaultPhase', 'profiles', 'profileDescriptionList']
        self.doNotSendToHardware += ['profileDescriptionList']
    
    def evaluate(self):
        if self.experiment.allow_evaluation:
            super(DDSchannel, self).evaluate()
            self.updateProfileDescriptionList()

    def updateProfileDescriptionList(self):
        if self.profiles is not None:
            #sets the descriptions shown in the combo box in the GUI
            pdl = ['{} {}'.format(i, n.description) for i,n in enumerate(self.profiles)]
            try:
                deferred_call(setattr, self, 'profileDescriptionList', pdl)
            except RuntimeError:
                #the GUI is not yet active
                self.profileDescriptionList = pdl

class RAMStaticPoint(Prop):
    """ Used to send one point for the RAM static array to the LabView controller.
    fPhiA stores the frequency, phase, or amplitude
    Mag stores the polar magnitude

    These are used in a ListProp, which is passed to labview as an nx2 array.
    It is transposed in LabView to a 2xn array, with the first row as f/phi/A and the 2nd row as Mag.
    """

    fPhiA = Float()
    Mag = Float()

    def toHardware(self):
        return '{} {}\n'.format(fPhiA, Mag)

class DDSprofile(Prop):
    frequency = Typed(FloatProp)
    amplitude = Typed(FloatProp)
    phase = Typed(FloatProp)
    RAMMode = Typed(StrProp)
    ZeroCrossing = Typed(BoolProp)
    NoDwellHigh = Typed(BoolProp)
    FunctionOrStatic = Typed(BoolProp)
    RAMFunction = Typed(StrProp)
    RAMInitialValue = Typed(FloatProp)
    RAMStepValue = Typed(FloatProp)
    RAMTimeStep = Typed(FloatProp)
    RAMNumSteps = Typed(IntProp)
    RAMStaticArray = Typed(ListProp)
    channel = Member()
    
    def __init__(self,name,experiment,description='',channel=None):
        self.channel=channel
        super(DDSprofile,self).__init__(name,experiment,description)
        self.frequency=FloatProp('frequency',self.experiment,'[MHz]','0')
        self.amplitude=FloatProp('amplitude',self.experiment,'[dBm]','0')
        self.phase=FloatProp('phase',self.experiment,'[rad]','0')
        self.RAMMode=StrProp('RAMMode',self.experiment,'','"Direct Switch"')
        self.ZeroCrossing=BoolProp('ZeroCrossing',self.experiment,'','False')
        self.NoDwellHigh=BoolProp('NoDwellHigh',self.experiment,'','False')
        self.FunctionOrStatic=BoolProp('FunctionOrStatic',self.experiment,'True=function, False=static','False')
        self.RAMFunction=StrProp('RAMFunction',self.experiment,'','""')
        self.RAMInitialValue=FloatProp('RAMInitialValue',self.experiment,'','0')
        self.RAMStepValue=FloatProp('RAMStepValue',self.experiment,'','0')
        self.RAMTimeStep=FloatProp('RAMTimeStep',self.experiment,'[us]','0')
        self.RAMNumSteps=IntProp('RAMNumSteps',self.experiment,'','0')
        self.RAMStaticArray=ListProp('RAMStaticArray', self.experiment, listElementType=RAMStaticPoint, listElementName='point')
        self.properties+=['frequency','amplitude','phase','RAMMode','ZeroCrossing','NoDwellHigh',
            'FunctionOrStatic','RAMFunction','RAMInitialValue','RAMStepValue','RAMTimeStep','RAMNumSteps','RAMStaticArray']
        self.doNotSendToHardware+=['RAMFunction','RAMInitialValue','RAMStepValue','RAMTimeStep','RAMNumSteps','RAMStaticArray']

    @observe('description')
    def descriptionChanged(self, change):
        self.channel.updateProfileDescriptionList()
    
    #override from Prop to give special formating of RAMFunction and RAMStaticArray.  They are in doNotSendToHardware, so they will not otherwise be sent
    def toHardware(self):
        '''This function provides generic hardware communication XML for this package.  It is similar to toXML(self),
        but in the end it puts out str(value) of each property, which is useful to the hardware, and does not put out any of the
        function information that leads to those values.'''
        output=''
        
        #go through list of single properties:
        for p in self.properties: # I use a for loop instead of list comprehension so I can have more detailed error reporting.
            if p not in self.doNotSendToHardware:
                #convert the string name to an actual object
                try:
                    o = getattr(self, p)
                except:
                    logger.warning('In Prop.toHardware() for class '+self.name+': item '+p+' in properties list does not exist.\n')
                    continue
                
                output+=self.HardwareProtocol(o, p)
        
        #special formatting for RAMFunction
        output += '<RAMFunction>{}\t{}\t{}\t{}\t{}</RAMFunction>'.format(self.RAMFunction.value, self.RAMInitialValue.value, self.RAMStepValue.value, self.RAMTimeStep.value, self.RAMNumSteps.value)
        output += '<RAMStaticArray>{}</RAMStaticArray>'.format('\t'.join([i.value for i in self.RAMStaticArray]))
        
        try:
            return '<{}>{}</{}>\n'.format(self.name, output, self.name)
        except Exception as e:
            logger.warning('While in format() in DDSProfile.toHardware() in '+self.name+'.\n'+str(e)+'\n')
            return ''
