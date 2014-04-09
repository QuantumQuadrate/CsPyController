'''camera.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-01-17
modified>=2014-01-17

This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
'''

from cs_errors import PauseError, setupLog
logger=setupLog(__name__)

from atom.api import Typed, Str
from instrument_property import Prop, BoolProp, IntProp, FloatProp, StrProp, ListProp, IntRangeProp, FloatRangeProp, EnumProp
from cs_instruments import Instrument

#---- instrument ----

class Camera(Instrument):
    enable=Typed(BoolProp)
    saveAsPNG=Typed(BoolProp)
    saveAsASCII=Typed(BoolProp)
    
    def __init__(self,experiment):
        super(Camera,self).__init__('camera',experiment)
        self.enable=BoolProp('enable',experiment,'enable camera','False')
        self.saveAsPNG=BoolProp('saveAsPNG',experiment,'save pictures as PNG','False')
        self.saveAsASCII=BoolProp('saveAsASCII',experiment,'save pictures as ASCII','False')
        self.properties+=['enable','saveAsPNG','saveAsASCII']
        self.doNotSendToHardware+=['saveAsPNG','saveAsASCII']

class HamamatsuC9100_13(Camera):
    version='2014.01.17'
    forceImagesToU16=Typed(BoolProp)
    EMGain=Typed(IntRangeProp)
    analogGain=Typed(IntRangeProp)
    exposureTime=Typed(FloatRangeProp)
    scanSpeed=Typed(EnumProp)
    lowLightSensitivity=Typed(EnumProp)
    externalTriggerMode=Typed(EnumProp)
    triggerPolarity=Typed(EnumProp)
    externalTriggerSource=Typed(EnumProp)
    cooling=Typed(EnumProp)
    fan=Typed(EnumProp)
    scanMode=Typed(EnumProp)
    photoelectronScaling=Typed(FloatProp)
    subArrayLeft=Typed(EnumProp)
    subArrayTop=Typed(EnumProp)
    subArrayWidth=Typed(EnumProp)
    subArrayHeight=Typed(EnumProp)
    superPixelBinning=Typed(EnumProp)
    frameGrabberAcquisitionRegionLeft=Typed(IntRangeProp)
    frameGrabberAcquisitionRegionTop=Typed(IntRangeProp)
    frameGrabberAcquisitionRegionRight=Typed(IntRangeProp)
    frameGrabberAcquisitionRegionBottom=Typed(IntRangeProp)
    numImageBuffers=Typed(IntRangeProp)
    shotsPerMeasurement=Typed(IntRangeProp)
    
    #regions of interest will be dealt with in a post-processing filter
    
    
    def __init__(self,experiment):
        super(HamamatsuC9100_13,self).__init__(experiment)
        
        self.forceImagesToU16=BoolProp('forceImagesToU16',experiment,'convert images to U16 (necessary on Aquarius hardware)','False')
        self.EMGain=IntRangeProp('EMGain',experiment,'EMCCD gain','0',low=0,high=255)
        self.analogGain=IntRangeProp('analogGain',experiment,'analog gain','0',low=0,high=5)
        self.exposureTime=FloatRangeProp('exposureTime',experiment,'exposure time (seconds)','00.050',low=.000001,high=7200) #low is 10 us, high is 7200 s, this setting does not apply if trigger is set to "level"
        self.scanSpeed=EnumProp('scanSpeed',experiment,'CCD readout scan speed','"High"',['Slow','Middle','High'])
        self.lowLightSensitivity=EnumProp('lowLightSensitivity',experiment,'low light sensitivity','"Off"',['Off','5x','13x','21x'])
        self.externalTriggerMode=EnumProp('externalTriggerMode',experiment,'external trigger mode','"Level"',['Edge','Level','Synchronous Readout'])
        self.triggerPolarity=EnumProp('triggerPolarity',experiment,'trigger polarity','"Positive"',['Positive','Negative'])
        self.externalTriggerSource=EnumProp('externalTriggerSource',experiment,'external trigger source','"BNC on Power Supply"',['Multi-Timing I/O Pin','BNC on Power Supply','CameraLink Interace'])
        self.cooling=EnumProp('cooling',experiment,'TEC cooling','"Off"',['Off','On'])
        self.fan=EnumProp('fan',experiment,'fan','"Off"',['Off','On'])
        self.scanMode=EnumProp('scanMode',experiment,'scan mode','"Normal"',['Normal','Super pixel','Sub-array'])
        self.photoelectronScaling=FloatProp('photoelectronScaling',experiment,'photoelectron scaling','1')
        self.subArrayLeft=EnumProp('subArrayLeft',experiment,'sub-array.left','0',range(0,512,16))
        self.subArrayTop=EnumProp('subArrayTop',experiment,'sub-array.top','0',range(0,512,16))
        self.subArrayWidth=EnumProp('subArrayWidth',experiment,'sub-array.width','512',range(16,513,16))
        self.subArrayHeight=EnumProp('subArrayHeight',experiment,'sub-array.height','512',range(16,513,16))
        self.superPixelBinning=EnumProp('superPixelBinning',experiment,'super pixel binning','"1x1"',['1x1','2x2','4x4'])
        self.frameGrabberAcquisitionRegionLeft=IntRangeProp('frameGrabberAcquisitionRegionLeft',experiment,'frameGrabberAcquisitionRegion.Left','0',low=0,high=512)
        self.frameGrabberAcquisitionRegionTop=IntRangeProp('frameGrabberAcquisitionRegionTop',experiment,'frameGrabberAcquisitionRegion.Top','0',low=0,high=512)
        self.frameGrabberAcquisitionRegionRight=IntRangeProp('frameGrabberAcquisitionRegionRight',experiment,'frameGrabberAcquisitionRegion.Right','512',low=0,high=512)
        self.frameGrabberAcquisitionRegionBottom=IntRangeProp('frameGrabberAcquisitionRegionBottom',experiment,'frameGrabberAcquisitionRegion.Bottom','512',low=0,high=512)
        self.numImageBuffers=IntRangeProp('numImageBuffers',experiment,'number of image buffers','300',low=0)
        self.shotsPerMeasurement=IntRangeProp('shotsPerMeasurement',experiment,'shots per measurement','1',low=0)
        
        self.properties+=['version','forceImagesToU16','EMGain','analogGain','exposureTime','scanSpeed','lowLightSensitivity',
        'externalTriggerMode','triggerPolarity','externalTriggerSource','cooling','fan','scanMode','photoelectronScaling',
        'subArrayLeft','subArrayTop','subArrayWidth','subArrayHeight','superPixelBinning','frameGrabberAcquisitionRegionLeft',
        'frameGrabberAcquisitionRegionTop','frameGrabberAcquisitionRegionRight','frameGrabberAcquisitionRegionBottom',
        'numImageBuffers','shotsPerMeasurement']
        self.doNotSendToHardware+=['photoelectronScaling']


class Andor(Camera):
    andorPath=Typed(StrProp)
    copyAndorFiles=Typed(BoolProp)
    msWaitTimeBeforeCopyingAndorFiles=Typed(FloatProp)
    
    def __init__(self):
            andorPath=StrProp('andorPath',experiment,'Where to find the saved Andor image files',r'C:\Users\QC\Documents\Cesium_project\Andor_picutres_temp')
            copyAndorFiles=BoolProp('copyAndorFiles',experiment,'should we copy Ander files into the experiment directory?','False')
            msWaitTimeBeforeCopyingAndorFiles=FloatProp('msWaitTimeBeforeCopyingAndorFiles',experiment,'how long to wait before copying Andor files (in ms)','0')