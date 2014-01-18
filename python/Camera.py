'''camera.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-01-17
modified>=2014-01-17

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

#from cs_errors import PauseError
from atom.api import Bool, Typed, Str, Int, Member
#from enthought.chaco.api import ArrayPlotData, Plot #for chaco plot
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp
from cs_instruments import Instrument
import matplotlib.pyplot as plt
import numpy, logging
logger = logging.getLogger(__name__)

from digital_waveform import Waveform, Channels
#import digital_waveform #my helper class for making Chaco plots of waveforms

#---- camera properties ----
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
        

#---- HSDIO instrument ----

class Camera(Instrument):
    enable=Typed(BoolProp)
    saveAsPNG=Typed(BoolProp)
    saveAsASCII=Typed(BoolProp)
    
    def __init__(self,experiment):
        super(Camera,self).__init__('Camera',experiment)
        self.enable=BoolProp('enable',experiment,'enable camera','False')
        self.saveAsPNG=BoolProp('saveAsPNG',experiment,'save pictures as PNG','False')
        self.saveAsASCII=BoolProp('saveAsASCII',experiment,'save pictures as ASCII','False')
        self.properties+=['enable','saveAsPNG','saveAsASCII']

class HamamatsuC9100_13(Camera):
    forceImagesToU16=Typed(BoolProp)
    EMGain=Type(IntRangeProp)

    # analogGain=Range(low=0,high=5,value=0)
    # exposureTime=FloatRange(low=.001,high=30000)
    # scanSpeed=Enum(['Slow','Middle','High'],'High')
    # lowLightSensitivity=Enum(['Off','5x','13x','21x'])
    # externalTriggerMode=Enum(['Edge','Level','Synchronous Readout'],'Level')
    # triggerPolarity=Enum(['Positive','Negative'],'Positive')
    # externalTriggerSource=Enum(['Multi-Timing I/O Pin','BNC on Power Supply','CameraLink Interace'],'BNC on Power Supply')
    # cooling=Enum(['Off','On'],'Off')
    # fan=Enum(['Off','On'],'Off')
    # scanMode=Enum(['Normal','Super pixel','Sub-array'],'Normal')
    # photoelectronScaling=Float(1)
    # subArrayLeft=Enum(range(0,512,16),0)
    # subArrayTop=Enum(range(0,512,16),0)
    # subArrayWidth=Enum(range(16,512,16),512)
    # subArrayHeight=Enum(range(16,512,16),512)
    # superPixelBinning=Enum(['1x1`','2x2','4x4'],'1x1')
    # frameGrabberAcquisitionRegionLeft=Range(low=0,high=512,value=0))
    # frameGrabberAcquisitionRegionTop=Range(low=0,high=512,value=0))
    # frameGrabberAcquisitionRegionRight=Range(low=0,high=512,value=512))
    # frameGrabberAcquisitionRegionBottom=Range(low=0,high=512,value=512))
    # numImageBuffers=Int(300)
    # shotsPerMeasurement=Int(1)
    
    #regions of interest will be dealt with in a post-processing filter
    
    version=Str()

    def __init__(self,experiment):
        super(HSDIO,self).__init__('HSDIO',experiment)
        
        self.version='2014.01.17'
        forceImagesToU16=BoolProp('forceImagesToU16',experiment,'convert images to U16 (necessary on Aquarius hardware)','False')
        EMGain=IntRangeProp('EMGain',experiment,'EMCCD gain','0',low=0,high=255)
        
        self.properties+=['version','forceImagesToU16','EMGain']
    
    def initialize(self):
        self.isInitialized=True

class Andor(Camera):
    andorPath=Str(r'C:\Users\QC\Documents\Cesium_project\Andor_picutres_temp')
    copyAndorFiles=Bool(False)
    msWaitTimeBeforeCopyingAndorFiles=Float(0)