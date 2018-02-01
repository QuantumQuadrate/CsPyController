"""andor.py
   Part of the AQuA Cesium Controller software package

   author=Martin Lichtman
   created=2014-07-28
   modified>=2014-07-30

   This code communicates with the Andor Luca camera.  It can both get and set
   the settings of the camera, and read images.  Single shot and video modes are
   supported.

   The dll interface in this code is based on:
   pyAndor - A Python wrapper for Andor's scientific cameras
   Copyright (C) 2009  Hamid Ohadi

   Andor class which is meant to provide the Python version of the same
   functions that are defined in the Andor's SDK. Since Python does not
   have pass by reference for immutable variables, some of these variables
   are actually stored in the class instance. For example the temperature,
   gain, gainRange, status etc. are stored in the class.

   """

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

from ctypes import CDLL, c_int, c_float, c_long, c_char_p, byref
import os, sys, threading, time
import numpy
from atom.api import Int, Tuple, List, Str, Float, Bool, Member, observe
from instrument_property import IntProp, FloatProp, ListProp, StrProp
from cs_instruments import Instrument

from PiParameterLookup import *
try:
    from PythonForPicam import *
except:
    logger.warning('''PythonForPicam not installed. Picam will not work. Run the following commands to install it:

    cd PythonForPicam
    python setup.py build
    python setup.py install

    ''')

# imports for viewer
from analysis import AnalysisWithFigure, Analysis
from colors import my_cmap
from enaml.application import deferred_call

def pointer(x):
    """Returns a ctypes pointer"""
    ptr = ctypes.pointer(x)
    return ptr


def load(x):
    """Loads DLL library where argument is location of library"""
    x = ctypes.cdll.LoadLibrary(x)
    return x


class PICamCamera(Instrument):

    AdcEMGain = Member()
    AdcAnalogGain = Int()
    exposureTime = Member()
    triggerMode = Int()
    acquisitionMode = Int()
    AdvancedEMGain = Int()
    EMGainMode = Int()
    binMode = Int()
    shotsPerMeasurement = Member()

    width = Int()  # the number of columns
    height = Int()  # the number of rows
    dim = Int()  # the total number of pixels
    serial = Int()  # the serial number of the camera
    c_image_array = Member()  # a c_int array to store incoming image data
    set_T = Int()
    temperature = Float()
    gain = Int()
    gainRange = Tuple()
    number_AD_channels = Int()
    bit_depths = List()
    channel = Int()
    outamp = Int()
    noHSSpeeds = Int()
    HSSpeeds = List()
    HSSpeed = Int()
    noVSSpeeds = Int()
    VSSpeeds = List()
    VSSpeed = Int()
    noGains = Int()
    preAmpGains = List()
    status = Str()
    accumulate = Float()
    kinetic = Float()
    available = Member()
    shutterMode = Int()
    useDemo = Bool()
    ReadoutControl = Int()
    readoutstride = Int()
    framestride = Int()
    framesize = Int()

    numPixX = Int()
    numPixY = Int()

    num_cameras = Member()
    currentHandleList = Member()
    currentHandleDict = Member()
    cameraIDList = Member()
    cameraIDDict = Member()
    cameraSerialList = Member()
    currentCamera = Member()
    currentSerial = Str()

    currentHandle = Member()
    currentID = Member()
    averageMeasurements = Bool()
    mostrecentresult = Member()

    data = Member()  # holds acquired images until they are written
    mode = Str('experiment')  # experiment vs. video
    analysis = Member()  # holds a link to the GUI display
    dll = Member()

    roilowh = Int(0)
    roihighh = Int(512)
    roilowv = Int(-512)
    roihighv = Int(0)
    roimaxh = Int(512)
    roimaxv = Int(-512)
    ROI = Member()
    enableROI = True

    autoscale = Bool(True)
    minPlot = Member()
    maxPlot = Member()

    triggerChoices = (6,7,1,0)     #6: edge trigger, 7: level trigger, 1: external, 0: internal
    acquisitionChoices = (1,2,3,4,5)
    binChoices = (1,2,4)

    def __init__(self, name, experiment, description=''):
        super(PICamCamera, self).__init__(name, experiment, description)
        self.AdcEMGain = IntProp('AdcEMGain', experiment, 'EM gain', '0')
        #self.AdcAnalogGain = IntProp('AdcAnalogGain', experiment, 'Analog gain', '0')
        self.exposureTime = FloatProp('exposureTime', experiment, 'exposure time for edge trigger (ms)', '0')
        self.shotsPerMeasurement = IntProp('shotsPerMeasurement', experiment, 'number of expected shots', '0')
        self.currentCamera = StrProp('currentCamera', experiment, 'Current Camera', '0')
        self.minPlot = IntProp('minPlot', experiment, 'Minimum Plot Scale Value', '0')
        self.maxPlot = IntProp('maxPlot', experiment, 'Maximum Plot Scale Value', '32768')
        self.properties += ['AdcEMGain', 'AdcAnalogGain', 'exposureTime', 'triggerMode', 'shotsPerMeasurement', 'minPlot', 'maxPlot',
                            'currentCamera', 'acquisitionMode', 'binMode', 'AdvancedEMGain', 'EMGainMode', 'numPixX', 'numPixY', 'useDemo', 'ReadoutControl', 'shutterMode', 'averageMeasurements',
                            'ROI', 'roilowv', 'roilowh', 'roihighv', 'roihighh']

    def __del__(self):
        if self.isInitialized:
            self.ShutDown()

    def initialize(self):
        """Starts the dll and finds the camera."""

        self.InitializeCamera()

        self.isInitialized = True

    def start(self):
        #if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == 0)):
        if self.isAcquisitionRunning():
            logger.warning('Aborting old acquisition')
            self.AbortAcquisition()
        self.StartAcquisition()
        self.isDone = True

    def update(self):
        if self.enable:
            self.mode = 'experiment'
            if not self.isInitialized:
                self.initialize()

            if self.isAcquisitionRunning():
                self.AbortAcquisition()

            self.sendparameters()

            if self.triggerMode == 0:
                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerDetermination, 3)
                self.DLLError(sys._getframe().f_code.co_name, error)

                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerResponse, 2)
                self.DLLError(sys._getframe().f_code.co_name, error)
            elif self.triggerMode == 1:
                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerDetermination, 4)
                self.DLLError(sys._getframe().f_code.co_name, error)

                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerResponse, 2)
                self.DLLError(sys._getframe().f_code.co_name, error)
            elif self.triggerMode == 2:
                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerDetermination, 1)
                self.DLLError(sys._getframe().f_code.co_name, error)

                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerResponse, 2)
                self.DLLError(sys._getframe().f_code.co_name, error)
            elif self.triggerMode == 3:
                error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerResponse, 1)
                self.DLLError(sys._getframe().f_code.co_name, error)

            error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_ShutterTimingMode, self.shutterMode+1)
            self.DLLError(sys._getframe().f_code.co_name, error)

            error = Picam_SetParameterLargeIntegerValue(self.currentHandle, PicamParameter_ReadoutCount, piint(self.shotsPerMeasurement.value))
            self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter ReadoutCount)', error)

            self.CreateAcquisitionBuffer()
            if not self.averageMeasurements:
                self.data = []
            if self.averageMeasurements:
                self.mostrecentresult = None

            failed_parameter_array_type = ctypes.POINTER(piint)
            failed_parameter_array = failed_parameter_array_type()
            failed_parameter_count = piint()
            error = Picam_CommitParameters(self.currentHandle, pointer(failed_parameter_array), byref(failed_parameter_count))
            err = self.DLLError(sys._getframe().f_code.co_name, error, True)
            if not err: #if DLLError reports an error
                if failed_parameter_count.value > 0:
                    logger.error('{} Parameters failed. Parameter {} failed.'.format(failed_parameter_count.value, failed_parameter_array[0]))
                    raise PauseError



    def setup_video_thread(self, analysis):
        thread = threading.Thread(target=self.setup_video, args=(analysis,))
        #thread.daemon = True
        thread.start()

    def addDemoCamera(self):
        print 'Adding Demo Camera'

        modelListType = ctypes.POINTER(PicamModel)
        modelList = modelListType()
        model_count = piint(0)
        Picam_GetAvailableDemoCameraModels(byref(modelList),byref(model_count))
        print "Available Demo Camera Model numbers:\n"
        for i in range(model_count.value):
            print modelList[i]
        print "\n"

        model = c_int(604)
        serial_number = c_char_p('Demo Cam 1')
        PicamID = PicamCameraID()
        print "ConnectDemoCamera returned: {}".format(Picam_ConnectDemoCamera(model,serial_number,pointer(PicamID)))
        self.printCameraID(PicamID)
        if self.useDemo:
            self.currentID = PicamID
            self.currentCamera.value = PicamID.serial_number
        return

    def printCameraID(self,PicamID):
        print "Camera Model: {}".format(PicamID.model)
        print "Camera computer interface is: {}".format(PicamID.computer_interface)
        print "Camera sensor name is: {}".format(PicamID.sensor_name)
        print "Camera serial number is: {}".format(PicamID.serial_number)
        return



    def sendparameters(self):
        self.GetDetector()
        
        if self.enableROI:
            self.setROIvalues()
            print "ROI: x={}, x_binning={}, y={}, y_binning={}, width={}, height={}".format(self.ROI.x, self.ROI.x_binning, self.ROI.y, self.ROI.y_binning, self.ROI.width, self.ROI.height)
            self.SetImage()
        else:
            self.setSingleROI()

        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_AdcAnalogGain, self.AdcAnalogGain+1)
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter AdcAnalogGain)', error)

        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_AdcEMGain, self.AdcEMGain.value)
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter AdcEMGain)', error)

        error = Picam_SetParameterFloatingPointValue(self.currentHandle, PicamParameter_ExposureTime, piflt(self.exposureTime.value))
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter ExposureTime)', error)


        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_CleanUntilTrigger, piint(1))
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter CleanUntilTrigger)', error)

        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_ReadoutControlMode, self.ReadoutControl+1)
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter ReadoutControlMode)', error)

    def setSingleROI(self):
        self.ROI = PicamRoi()
        self.ROI.x = 0
        self.ROI.y = 0
        self.ROI.width = 512
        self.ROI.height = 512
        self.ROI.x_binning = self.binChoices[self.binMode]
        self.ROI.y_binning = self.binChoices[self.binMode]
        self.width = self.ROI.width
        self.height = self.ROI.height
        self.dim = self.width*self.height

    def isAcquisitionRunning(self):
        running = pibln()
        error = Picam_IsAcquisitionRunning(self.currentHandle, byref(running))
        return running

    def setup_video(self, analysis):
        if self.experiment.status != 'idle':
            logger.warning('Cannot start video mode unless experiment is idle.')
            return
        self.mode = 'video'
        self.analysis = analysis

        previouslyenabled=self.enable
        self.enable=True
        self.experiment.evaluate()
        self.enable=previouslyenabled


        if not self.isInitialized:
            self.initialize()

        if self.isAcquisitionRunning():
            self.AbortAcquisition()

        self.sendparameters()

        error = Picam_SetParameterLargeIntegerValue(self.currentHandle, PicamParameter_ReadoutCount, piint(0))
        self.DLLError(str(sys._getframe().f_code.co_name) + ' (parameter ReadoutCount)', error)

        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerDetermination, piint(4))
        self.DLLError(sys._getframe().f_code.co_name, error)

        error = Picam_SetParameterIntegerValue(self.currentHandle, PicamParameter_TriggerResponse, piint(1))
        self.DLLError(sys._getframe().f_code.co_name, error)

        error = Picam_SetParameterLargeIntegerValue(self.currentHandle, PicamParameter_ReadoutCount, piint(1))
        self.DLLError(sys._getframe().f_code.co_name, error)

        self.commitParameters()

        if self.enableROI:
            self.setROIvalues()
            p6 = self.ROI.y_binning
            print "p6 = {}".format(p6)
            self.SetImage() 
        else:
            if self.binChoices[self.binMode] > 1:
                wid=(self.width / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
                high=(self.height / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
            else:
                wid=self.width
                high = self.height
            '''self.SetImage(
                self.binChoices[self.binMode],
                self.binChoices[self.binMode],
                1,
                wid,
                1,
                high)  # full sensor, no binning'''

        #print self.width, self.height, self.dim
        if self.binChoices[self.binMode] > 1:
            self.width = self.width / self.binChoices[self.binMode]
            self.height = self.height / self.binChoices[self.binMode]
            self.dim = self.width * self.height

        self.getReadoutStride()

        self.data = self.CreateAcquisitionBuffer()

        analysis.setup_video(self.data)
        # run the video loop in a new thread

        self.start_video_thread()
        #thread = threading.Thread(target=self.start_video_thread)
        #thread.daemon = True
        #thread.start()

    def SetImage(self):   
        ROIS = PicamRois(1)
        ROIS.roi_array[0] = self.ROI
        error = Picam_SetParameterRoisValue(self.currentHandle, PicamParameter_Rois, ROIS)
        self.DLLError(sys._getframe().f_code.co_name, error)
        return
        
        
        
    def commitParameters(self):
        failed_parameter_count = piint()
        failed_parameter_array = piint()
        error = Picam_CommitParameters(self.currentHandle, pointer(failed_parameter_array), byref(failed_parameter_count))
        err = self.DLLError(sys._getframe().f_code.co_name, error, True)
        if not err: #if DLLError reports an error
            if failed_parameter_count.value > 0:
                logger.error('Parameter {} failed.'.format(failed_parameter_array[0]))
                raise PauseError
        return

    def start_video_thread(self):
        while self.mode == 'video':
            if self.GetMostRecentImage():
                # if there is new data, then redraw image
                self.analysis.redraw_video()
            time.sleep(.1)

    def stop_video(self):
        # stop the video thread from looping
        self.mode = 'idle'
        time.sleep(.01)
        self.AbortAcquisition()

    def acquire_data(self):
        """Overwritten from Instrument, this function is called by the experiment after
                each measurement run to make sure all pictures have been acquired."""
        if self.enable:
            if not self.averageMeasurements:
                self.data = self.GetImages()
            else:
                data = self.GetImages()
                if self.mostrecentresult is not None:
                    self.data = self.mostrecentresult+numpy.array(data,dtype='u4')
                else:
                    self.data = numpy.array(data,dtype='u4')

    def writeResults(self, hdf5):
        """Overwritten from Instrument.  This function is called by the experiment after
        data acquisition to write the obtained images to hdf5 file."""
        if self.enable:
            try:
                self.mostrecentresult = self.data
                if (not self.averageMeasurements):# or (self.averageMeasurements and self.experiment.measurement == self.experiment.measurementsPerIteration):  #(Removed +1 after self.experiment.measurement)
                    logger.info("Writing data for PICam")
                    hdf5['PICam_{}'.format(self.currentSerial)] = self.data
            except Exception as e:
                logger.error('in PICam.writeResults:\n{}'.format(e))
                raise PauseError

    def writeResultsAverage(self, hdf5):
        """Overwritten from Instrument.  This function is called by the experiment after
        data acquisition to write the obtained images to hdf5 file."""
        if self.enable:
            try:
                self.mostrecentresult = self.data
                if (self.averageMeasurements):# or (self.averageMeasurements and self.experiment.measurement == self.experiment.measurementsPerIteration):  #(Removed +1 after self.experiment.measurement)
                    logger.info("Writing data for PICam")
                    hdf5['PICam_{}'.format(self.currentSerial)] = self.data
            except Exception as e:
                logger.error('in PICam.writeResults:\n{}'.format(e))
                raise PauseError                
                
    def SetSingleScan(self):
        self.SetReadMode(4)
        self.setSingleROI()
        self.SetImage()
        self.SetAcquisitionMode(1)
        self.SetTriggerMode(0)

    def SetVideoMode(self):
        self.SetReadMode(4)
        self.setSingleROI()
        self.SetImage()
        self.SetAcquisitionMode(5)
        self.SetKineticCycleTime(0)  # for run till abort mode
        self.SetTriggerMode(0)  # internal trigger

    def InitializeCamera(self):
        if (not self.experiment.PICams.isInitialized):
            self.experiment.PICams.initialize()
        if self.useDemo:
            self.addDemoCamera()
        #self.dll = self.experiment.PICams.dll
        self.isInitialized=True

        currentHandleListType = ctypes.POINTER(PicamCameraID)  #arbitrarily setting length = 10, since we don't know yet the number of cameras, and nobody would have more than 10 cameras, right?
        self.currentHandleList = currentHandleListType()
        self.num_cameras = piint(0)
        logger.debug( "Getting Available Camera IDs: {}".format(Picam_GetAvailableCameraIDs(byref(self.currentHandleList),byref(self.num_cameras))))
        logger.debug("Number of Princeton Instruments cameras detected: {}".format(self.num_cameras.value))
        self.printCameraID(self.currentHandleList[0])
        self.cameraIDDict = dict(zip([self.currentHandleList[i].serial_number for i in range(self.num_cameras.value)],range(self.num_cameras.value)))

        #try:
        print self.cameraIDDict
        self.currentID = self.currentHandleList[self.cameraIDDict[self.currentCamera.value]]

        #except Exception as e:
        #    logger.error("Invalid camera number: {}. Exception: {}".format(self.currentHandleDict[self.currentCamera.value],e))
        #    raise PauseError

        self.currentHandle = PicamHandle()

        error = Picam_OpenCamera(self.currentID, byref(self.currentHandle))
        self.DLLError(sys._getframe().f_code.co_name, error)

        self.currentSerial = self.currentID.serial_number



    def setCamera(self):
        if not self.isInitialized:
            self.initialize()


    def getCurrentSerialNumber(self):
        try:
            sn = self.currentID.serial_number
            return sn
        except Exception as e:
            return 'No serial number detected'


    def GetImages(self):
        #if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == self.experiment.measurementsPerIteration - 1)):
            #print "calling GetAcquiredData"
        data = self.GetAcquiredData()
        #self.StartAcquisition()
        return data
        return 0

    def setROIvalues(self):
        if self.ROI is None:
            self.setCamera()
            self.GetDetector()

        self.setSingleROI()
        self.ROI.x_binning = self.binChoices[self.binMode]   #x-binning

        self.ROI.x = min(self.roihighh,self.roilowh)   #x
        self.ROI.width = max(self.roihighh,self.roilowh) - self.ROI.x   #width
        self.ROI.y = min(-1*self.roihighv,-1*self.roilowv)   #x
        self.ROI.height = max(-1*self.roihighv,-1*self.roilowv) - self.ROI.y   #width

        self.ROI.y_binning = self.binChoices[self.binMode]   #y-binning

        self.width = self.ROI.width
        self.height = self.ROI.height

        self.dim = self.width*self.height
        #print "self.width: {} self.height: {}".format(self.width,self.height)
        #print "ROI: {}".format(self.ROI)


    def GetDetector(self):
        width = piint(0)
        height = piint(0)
        logger.info('self.currentHandle: {}'.format(self.currentHandle))
        logger.info('Getting detector width')
        error = Picam_GetParameterIntegerValue(self.currentHandle, c_int(PicamParameter_SensorActiveWidth), byref(width))
        self.DLLError(sys._getframe().f_code.co_name, error)

        logger.info('Width={}. Getting detector height'.format(width.value))
        error = Picam_GetParameterIntegerValue(self.currentHandle, PicamParameter_SensorActiveHeight, byref(height))
        self.DLLError(sys._getframe().f_code.co_name, error)

        logger.info('Height={}. Setting ROI'.format(height.value))
        self.width = width.value
        self.height = height.value  # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.dim = self.width * self.height

        self.roimaxv = -self.height
        self.roimaxh = self.width
        #self.width = self.width - 1
        #self.height = self.height - 1   # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.setSingleROI()
        #print 'Andor: width {}, height {}'.format(self.width, self.height)
        return self.width, self.height

    def DLLError(self, func, error, NoPause=False):
        if error != 'PicamError_None':
            logger.error('Error in {} on camera {}:\n{}'.format(func,error,self.currentCamera.value))
            if not NoPause:
                raise PauseError
            return False
        return True


    def AbortAcquisition(self):
        error = Picam_StopAcquisition(self.currentHandle)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def ShutDown(self):
        error = Picam_CloseCamera(self.currentHandle)
        self.DLLError(sys._getframe().f_code.co_name, error, True)

    def GetCameraSerialNumber(self):
        serial = c_int()
        error = self.dll.GetCameraSerialNumber(byref(serial))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.serial = serial.value
        return self.serial

    def getReadoutStride(self):
        readoutstride = piint(0);
        Picam_GetParameterIntegerValue( self.currentHandle, c_int(PicamParameter_ReadoutStride), byref(readoutstride) )

        framestride = piint(0);
        Picam_GetParameterIntegerValue( self.currentHandle, c_int(PicamParameter_FrameStride), byref(framestride) )

        framesize = piint(0);
        Picam_GetParameterIntegerValue( self.currentHandle, c_int(PicamParameter_FrameSize), byref(framesize) )

        self.readoutstride = readoutstride.value
        self.framestride = framestride.value
        self.framesize = framesize.value



    def StartAcquisition(self):
        logger.debug('Getting Readout Stride')
        self.getReadoutStride()

        logger.debug('Committing Parameters')
        self.commitParameters()

        logger.debug('Starting Acquisition')
        error = Picam_StartAcquisition(self.currentHandle)
        logger.debug('Started Acquisition')
        self.DLLError(sys._getframe().f_code.co_name, error)


    def GetAcquiredData(self, dump=False):
        #print "calling dll"
        status = PicamAcquisitionStatus()
        available_array_type = PicamAvailableData*self.shotsPerMeasurement.value
        self.available = available_array_type
        status.running = True
        readout_time_out = piint(100000)
        readoutnum = 0
        while status.running and readoutnum < self.shotsPerMeasurement.value:
            available = PicamAvailableData(0,0)
            error = Picam_WaitForAcquisitionUpdate(self.currentHandle, readout_time_out, byref(available), byref(status))
            logger.debug('Acquisition status: {}'.format(status.running))
            if status.errors != 0:
                logger.warning('Acquisition error {}'.format(status.errors))
            self.DLLError(sys._getframe().f_code.co_name, error, dump)
            readoutnum += available.readout_count

            self.getReadoutStride()
            sz = self.framesize/2

            logger.debug('Getting DataPointer. Readout_count={}'.format(available.readout_count))

            DataArrayPointerType = ctypes.POINTER(pi16u*sz)

            readout=0
            while readout < available.readout_count:
                DataPointer = ctypes.cast(available.initial_readout+self.framestride/2*readout,DataArrayPointerType)
                dat = DataPointer.contents

                try:
                    data = numpy.append(data, numpy.reshape(dat, (1, self.height, self.width)),axis=0)
                except:
                    try:
                        data = numpy.reshape(dat, (1, self.height, self.width))
                    except:
                        print "dat.shape={}".format(numpy.array(dat).shape)
                        print "available.readout_count={}, self.height={}, self.width={}, a*h*w={}".format(available.readout_count, self.height, self.width,available.readout_count*self.height*self.width)
                readout += 1
        self.AbortAcquisition()
        carp = PicamAvailableData(0,0)
        while status.running:
            error = Picam_WaitForAcquisitionUpdate(self.currentHandle, readout_time_out, byref(carp), byref(status))
            logger.debug('Acquisition status: {}'.format(status.running))
            if status.errors != 0:
                logger.warning('Acquisition error {}'.format(status.errors))
        if carp.readout_count > 0:
            logger.warning ('{} Discarded Readout. Triggering issue?'.format(carp.readout_count))


        logger.debug('data.shape = {}'.format(data.shape))
        return data

    def CreateAcquisitionBuffer(self):
        """This function creates an image buffer to be used for video display.
        The buffer will be updated by the GetMostRecentImage method, to give the fastest
        possible update.  A numpy array that uses the same memory space as the c array is returned.
        That way plotting functions like matplotlib can be used and the plot data can be
        automatically updated whenever new data is available.  All that needs to be done is for the
        plot to be redrawn whenever a new image is captured."""

        try:
            c_image_array_type = pi16u * self.dim
            self.c_image_array = c_image_array_type()

            data = numpy.ctypeslib.as_array(self.c_image_array)
            data = numpy.reshape(data, (self.height, self.width))
        except Exception as e:
            logger.error("Exception in CreateAcquisitionBuffer: {}".format(e))
            logger.error("dim={} height={} width={}".format(self.dim,self.height,self.width))
            logger.error("data shape: {}".format(data.shape))
            raise PauseError
        self.available = PicamAvailableData(0,0)
        self.data = data
        return data

    def GetMostRecentImage(self):
        """This function gets the most recent image, for video display.
        It must be preceded by a call to CreateAcquisitionBuffer() and StartAcquisition().
        The image data is put into self.c_image_array, which must already be allocated (by Create AcquisitionBuffer)."""
        errors = PicamAcquisitionErrorsMask()
        self.available = PicamAvailableData(0,0)
        logger.debug('About to acquire image')
        error = Picam_Acquire(self.currentHandle, piint(1), piint(10000), byref(self.available), byref(errors))
        logger.debug('Acquired image')

        sz = self.framesize/2
        DataArrayType = pi16u*sz

        DataArrayPointerType = ctypes.POINTER(pi16u*sz)
        DataPointer = ctypes.cast(self.available.initial_readout,DataArrayPointerType)

        try:
            self.c_image_array[:] = DataPointer.contents
        except Exception as e:
            return False

        return self.DLLError(sys._getframe().f_code.co_name, error, True)



class PICamViewer(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    shot = Int(0)
    update_lock = Bool(False)
    artist = Member()
    mycam=Member()
    ax = Member()
    bgsub = Bool(False)
    draw_fig = Bool(True)

    maxPixel = Int(0)
    meanPixel = Int(0)

    def __init__(self, name, experiment, description,camera):
        super(PICamViewer, self).__init__(name, experiment, description)
        self.properties += ['shot', 'bgsub', 'draw_fig']
        self.mycam=camera

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        #print "analyzeMeasurement: Looking for 'data/PICam_{}'".format(self.mycam.currentHandle)
        if 'data/PICam_{}'.format(self.mycam.currentSerial) in measurementResults:
            #for each image
            self.data = measurementResults['data/PICam_{}'.format(self.mycam.currentSerial)]
        elif self.mycam.averageMeasurements:
            self.data = self.mycam.mostrecentresult
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if self.draw_fig:
            if not self.update_lock and (self.mycam.mode != 'video'):
                try:
                    self.update_lock = True
                    try:
                        xlimit = numpy.array(self.ax.get_xlim(), dtype = int)
                        ylimit = numpy.array(self.ax.get_ylim(), dtype = int)
                        limits = True
                    except:
                        limits = False
                    fig = self.backFigure
                    fig.clf()

                    if (self.data is not None) and (self.shot < len(self.data)):
                        ax = fig.add_subplot(111)
                        self.ax = ax
                        if self.bgsub and len(self.data)>1:
                            mydat = - numpy.array(self.data[1],dtype='u4').astype(numpy.int32) + numpy.array(self.data[0],dtype='u4').astype(numpy.int32)
                        else:
                            mydat = self.data[self.shot]
                        if (not self.mycam.autoscale):
                            ax.matshow(mydat, cmap=my_cmap, vmin=self.mycam.minPlot.value, vmax=self.mycam.maxPlot.value)
                        else:
                            ax.matshow(mydat, cmap=my_cmap)
                        if self.bgsub and len(self.data)>1:
                            ax.set_title('Background-subtracted shot')
                        else:
                            ax.set_title('most recent shot '+str(self.shot))

                        if limits:
                            ax.set_xlim(xlimit[0],xlimit[1])
                            ax.set_ylim(ylimit[0],ylimit[1])

                        #print "Max: {}".format(numpy.max(mydat))
                        #print "Min: {}".format(numpy.min(mydat))
                        self.maxPixel = int(numpy.max(self.data[self.shot]))
                        self.meanPixel = int(numpy.mean(self.data[self.shot]))
                    super(PICamViewer, self).updateFigure()
                except Exception as e:
                    logger.warning('Problem in PICamViewer.updateFigure()\n:{}'.format(e))
                finally:
                    self.update_lock = False

    def setup_video(self, data):
        """Use this method to connect the analysis figure to an array that will be rapidly updated
        in video mode."""
        self.data = data
        fig = self.backFigure
        fig.clf()
        ax = fig.add_subplot(111)

        self.artist = ax.imshow(data, vmin=self.mycam.minPlot.value, vmax=self.mycam.maxPlot.value)
        super(PICamViewer, self).updateFigure()

    def redraw_video(self):
        """First update self.data using Andor methods, then redraw screen using this."""
        if (self.mycam.autoscale):
            self.artist.set_data(self.data)
            self.artist.autoscale()
        else:
            self.artist.set_data(self.data)
        deferred_call(self.figure.canvas.draw)
        self.maxPixel = int(numpy.max(self.data))              #What does "shot" mean in video mode?
        self.meanPixel = int(numpy.mean(self.data))



class PICam(Instrument):
    camera = Member()
    analysis = Member()

    def __init__(self, name, experiment, description=''):
        super(PICam, self).__init__(name, experiment, description)
        self.camera = PICamCamera('Camera{}'.format(name),experiment,'PICam Camera')
        self.analysis = PICamViewer('Viewer{}'.format(name),experiment,'PICam Viewer',self.camera)
        self.properties += ['camera','analysis']

    def evaluate(self):
        self.camera.evaluate()


class PICams(Instrument,Analysis):
    version = '2016.06.02'
    motors = Member()
    dll = Member()

    def __init__(self, name, experiment, description=''):
        super(PICams, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Princeton Instruments cameras', listElementType=PICam,
                               listElementName='motor')
        self.properties += ['version', 'motors']
        self.initialize(True)

    def initializecameras(self):
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.initialize()
        except Exception as e:
            logger.error('Problem initializing Princeton Instruments camera:\n{}\n{}\n'.format(msg,e))
            self.isInitialized = False
            raise PauseError

    def initialize(self, cameras=False):
        msg=''
        # TODO: if you want to be able to dynamically change this it has to not
        # set the DLL path during initialization
        dllpath = r'D:\git\cspycontroller\python\PythonForPicam\DLLs\Picam.dll'#self.experiment.Config.config.get('PICAM', 'PICAM_DLL')
        #self.dll = load(dllpath)
        try:
            logger.debug("Initializing Picam library: {}".format(Picam_InitializeLibrary()))
        except NameError as e:
            # no dll found
            logger.warning("Cannot Initialize Picam library: No dll found at {}. {}".format(dllpath,e))
            self.enable = False
            self.isInitialized = False
        else:
            self.enable = True
            self.isInitialized = True
            if (cameras):
                self.initializecameras()

    def start(self):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.start()
        except Exception as e:
            logger.error('Problem starting Princeton Instruments camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

        self.isDone = True




    def update(self):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.update()
        except Exception as e:
            logger.error('Problem updating Princeton Instruments camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def evaluate(self):
        msg = ''
        try:
            for i in self.motors:
                msg = i.evaluate()
        except Exception as e:
            logger.error('Problem evaluating Princeton Instruments camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def writeResults(self, hdf5):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.writeResults(hdf5)
        except Exception as e:
            logger.error('Problem writing Princeton Instruments camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def acquire_data(self):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.acquire_data()
        except Exception as e:
            logger.error('Problem acquiring Princeton Instruments camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def __del__(self):
        if self.isInitialized:
            for i in self.motors:
                try:
                    if i.camera.isAcquisitionRunning():
                        i.camera.AbortAcquisition()
                except Exception as e:
                    logger.warning("Error in ShutDown: {}".format(e))
            try:
                error = self.dll.ShutDown()
                if ERROR_CODE[error] != 'DRV_SUCCESS':
                    logger.error('Error in ShutDown:\n{}'.format(ERROR_CODE[error]))
            except Exception as e:
                logger.warning("Error in ShutDown: {}".format(e))


    def analyzeMeasurement(self,measurementresults,iterationresults,hdf5):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.analysis.analyzeMeasurement(measurementresults,iterationresults,hdf5)
        except Exception as e:
            logger.error('Problem displaying Princeton Instruments camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError
        return 0
        
    def analyzeIteration(self,iterationResults,experimentResults):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.writeResultsAverage(iterationResults)
        except Exception as e:
            logger.error('Problem writing Princeton Instruments camera data at end of iteration:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError
        super(PICams,self).analyzeIteration(iterationResults, experimentResults)
        
    def postExperiment(self,experimentresults):
        # We have been unable to figure out why during the postExperiment call
        # the enable is set to False for PICams.  This is a shitty patch (DB & MFE)
        temp_enable = self.enable
        super(PICams,self).postExperiment(experimentresults)
        self.enable = temp_enable
