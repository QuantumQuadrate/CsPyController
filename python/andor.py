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
from instrument_property import IntProp, FloatProp, ListProp
from cs_instruments import Instrument

# imports for viewer
from analysis import AnalysisWithFigure, Analysis
from colors import my_cmap
from enaml.application import deferred_call

class AndorCamera(Instrument):

    EMCCDGain = Member()
    preAmpGain = Member()
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

    numPixX = Int()
    numPixY = Int()

    num_cameras = c_long()
    cameraHandleList = Member()
    cameraHandleDict = Member()
    cameraSerialList = Member()
    currentCamera = Member()

    CurrentHandle = Int()

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
    enableROI = False

    autoscale = Bool(True)
    minPlot = Member()
    maxPlot = Member()

    triggerChoices = (6,7,1,0)     #6: edge trigger, 7: level trigger, 1: external, 0: internal
    acquisitionChoices = (1,2,3,4,5)
    binChoices = (1,2,4)

    def __init__(self, name, experiment, description=''):
        super(AndorCamera, self).__init__(name, experiment, description)
        self.EMCCDGain = IntProp('EMCCDGain', experiment, 'Andor EM gain', '0')
        self.preAmpGain = IntProp('preAmpGain', experiment, 'Andor analog gain', '0')
        self.exposureTime = FloatProp('exposureTime', experiment, 'exposure time for edge trigger', '0')
        self.shotsPerMeasurement = IntProp('shotsPerMeasurement', experiment, 'number of expected shots', '0')
        self.currentCamera = IntProp('currentCamera', experiment, 'Current Camera', '0')
        self.minPlot = IntProp('minPlot', experiment, 'Minimum Plot Scale Value', '0')
        self.maxPlot = IntProp('maxPlot', experiment, 'Maximum Plot Scale Value', '32768')
        self.properties += ['EMCCDGain', 'preAmpGain', 'exposureTime', 'triggerMode', 'shotsPerMeasurement', 'minPlot', 'maxPlot',
                            'currentCamera', 'acquisitionMode', 'binMode', 'AdvancedEMGain', 'EMGainMode', 'numPixX', 'numPixY',
                            'ROI', 'roilowv', 'roilowh', 'roihighv', 'roihighh']

    def __del__(self):
        if self.isInitialized:
            self.ShutDown()

    def initialize(self):
        """Starts the dll and finds the camera."""

        self.InitializeCamera()
        self.GetCameraSerialNumber()
        self.SetCoolerMode(1)
        self.CoolerON()
        self.dll.SetFanMode(0)

        #time.sleep(1)
        self.isInitialized = True

    def start(self):
        #get images to clear out any old images
        #if self.GetStatus() == 'DRV_ACQUIRING':
        #    self.AbortAcquisition()
        #self.DumpImages()
        #declare that we are done now
        if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == 0)):
            self.setCamera()
            self.GetTemperature()
            if self.GetStatus() == 'DRV_ACQUIRING':
                    self.GetAcquiredData(True)
                    self.AbortAcquisition()
            self.StartAcquisition()
            self.isDone = True

    def update(self):
        if self.enable:
            self.setCamera()
            #print "Updating Andor camera {}".format(self.CurrentHandle)
            self.mode = 'experiment'
            if self.GetStatus() == 'DRV_ACQUIRING':
                self.GetAcquiredData(True)
                self.AbortAcquisition()
            self.GetDetector()
            self.GetTemperature()

            self.SetAcquisitionMode(self.acquisitionChoices[self.acquisitionMode])
            self.SetReadMode(4)  # image mode
            self.SetExposureTime(self.exposureTime.value)
            exposure,accumulate , kinetic = self.GetAcquisitionTimings()
            #print "Values returned by GetAcquisitionTimings: exposure: {}, accumulate:{}, kinetic: {}".format(exposure,accumulate,kinetic)
            self.SetTriggerMode(self.triggerChoices[self.triggerMode])

            #print "bin size: {}".format(self.binChoices[self.binMode])
            #self.SetImage(1,1,1,self.width,1,self.height)
            #print "done setImage"
            self.SetImage(
                self.binChoices[self.binMode],
                self.binChoices[self.binMode],
                1,
                (self.width / self.binChoices[self.binMode]) * self.binChoices[self.binMode],
                1,
                (self.height / self.binChoices[self.binMode]) * self.binChoices[self.binMode])  # full sensor, no binning
            self.numPixX = (self.width / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
            self.numPixY = (self.width / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
            if self.binChoices[self.binMode] > 1:
                self.width = self.width / self.binChoices[self.binMode]
                self.height = self.height / self.binChoices[self.binMode]
                self.dim = self.width * self.height
            #print "done setImage. With binning of {}, new width and height are {}, {}".format(self.binChoices[self.binMode],self.width,self.height)
            if (self.acquisitionChoices[self.acquisitionMode]==3 or self.acquisitionChoices[self.acquisitionMode]==4):
                self.SetNumberKinetics(self.shotsPerMeasurement.value)
                #print "done setNumberKinetics"
            if (self.acquisitionChoices[self.acquisitionMode]!=1 and self.acquisitionChoices[self.acquisitionMode]!=4):
                self.SetFrameTransferMode(0)
                #print "done SetFrameTransferMode"
            if (self.acquisitionChoices[self.acquisitionMode]==2):
                self.SetNumberAccumulations(self.experiment.measurementsPerIteration)
            self.SetKineticCycleTime(0)  # no delay
            self.SetEMGainMode(self.EMGainMode)
            self.SetEMAdvanced(self.AdvancedEMGain)
            self.SetPreAmpGain(self.preAmpGain.value)
            self.SetEMCCDGain(self.EMCCDGain.value)
            self.dll.EnableKeepCleans(1)
            self.SetImageFlip(0,1)
            currentgain = self.GetEMCCDGain()
            gain_range = self.GetEMGainRange()
            #print "EMGainRange: {}".format(gain_range)
            exposure,accumulate , kinetic = self.GetAcquisitionTimings()
        #else:
        #    print "Andor camera {} is not enabled".format(self.CurrentHandle)

    def setup_video_thread(self, analysis):
        thread = threading.Thread(target=self.setup_video, args=(analysis,))
        #thread.daemon = True
        thread.start()

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
        self.setCamera()
        if self.GetStatus() == 'DRV_ACQUIRING':
            self.AbortAcquisition()
        self.GetDetector()
        self.SetPreAmpGain(self.preAmpGain.value)
        self.SetEMCCDGain(self.EMCCDGain.value)
        self.SetExposureTime(self.exposureTime.value)
        self.SetTriggerMode(0)
        self.SetReadMode(4)  # image mode
        #print "bin size: {}".format(self.binChoices[self.binMode])


        if self.enableROI:
            self.setROIvalues()
            p6 = self.ROI[4]
            print "p6 = {}".format(p6)
            self.SetImage(
                self.binChoices[self.binMode],
                self.binChoices[self.binMode],
                max(self.ROI[0],1),
                self.ROI[1],
                max(self.ROI[3],1),
                p6)  # full sensor, no binning
        else:
            if self.binChoices[self.binMode] > 1:
                wid=(self.width / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
                high=(self.height / self.binChoices[self.binMode]) * self.binChoices[self.binMode]
            else:
                wid=self.width
                high = self.height
            self.SetImage(
                self.binChoices[self.binMode],
                self.binChoices[self.binMode],
                1,
                wid,
                1,
                high)  # full sensor, no binning
        self.SetAcquisitionMode(5)  # run till abort
        self.SetKineticCycleTime(0)  # no delay

        #print self.width, self.height, self.dim
        if self.binChoices[self.binMode] > 1:
            self.width = self.width / self.binChoices[self.binMode]
            self.height = self.height / self.binChoices[self.binMode]
            self.dim = self.width * self.height
        self.data = self.CreateAcquisitionBuffer()
        self.SetImageFlip(0,1)
        analysis.setup_video(self.data)

        self.StartAcquisition()

        # run the video loop in a new thread
        self.start_video_thread()
        #thread = threading.Thread(target=self.start_video_thread)
        #thread.daemon = True
        #thread.start()

    def start_video_thread(self):
        while self.mode == 'video':
            self.setCamera()
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
            if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == self.experiment.measurementsPerIteration - 1)):
                self.setCamera()
                self.data = self.GetImages()

    def writeResults(self, hdf5):
        """Overwritten from Instrument.  This function is called by the experiment after
        data acquisition to write the obtained images to hdf5 file."""
        logger.debug("Writing results from Andor to Andor_{}".format(self.CurrentHandle))
        if self.enable:
            if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == self.experiment.measurementsPerIteration - 1)):
                try:
                    hdf5['Andor_{}'.format(self.CurrentHandle)] = self.data
                except Exception as e:
                    logger.error('in Andor.writeResults:\n{}'.format(e))
                    raise PauseError

    def SetSingleScan(self):
        self.SetReadMode(4)
        self.SetImage(1, 1, 1, self.width, 1, self.height)
        self.SetAcquisitionMode(1)
        self.SetTriggerMode(0)

    def SetVideoMode(self):
        self.SetReadMode(4)
        self.SetImage(1, 1, 1, self.width, 1, self.height)
        self.SetAcquisitionMode(5)
        self.SetKineticCycleTime(0)  # for run till abort mode
        self.SetTriggerMode(0)  # internal trigger

    def InitializeCamera(self):
        if (not self.experiment.Andors.isInitialized):
            self.experiment.Andors.initialize()
        self.dll = self.experiment.Andors.dll
        self.isInitialized=True


        error = self.experiment.Andors.dll.GetAvailableCameras(byref(self.num_cameras))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error getting number of Andor cameras:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        logger.warning("Number of Andor cameras detected: {}".format(self.num_cameras.value))

        cameraHandleListType = c_long * self.num_cameras.value
        self.cameraHandleList = cameraHandleListType()
        for cameranum in range(0,self.num_cameras.value):
            camHandle=c_long()
            error = self.dll.GetCameraHandle(c_long(cameranum),byref(camHandle))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error getting Andor camera handle:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            self.cameraHandleList[cameranum]=camHandle
            #logger.warning("Handle for Camera {}: {}".format(cameranum,camHandle.value))

        self.getAllSerials()

        self.setCamera()

    def getAllSerials(self):
        self.cameraSerialList = numpy.zeros(self.num_cameras.value, dtype=numpy.int)
        camSerial = c_int()
        for camnum in range(0,self.num_cameras.value):

            error = self.dll.SetCurrentCamera(self.cameraHandleList[camnum])
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error in getAllSerials setting Andor camera {}, handle {}:\n{}'.format(camnum,self.cameraHandleList[camnum],ERROR_CODE[error]))
                raise PauseError
            currentcam = c_int()
            error = self.dll.GetCurrentCamera(byref(currentcam))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error in getAllSerials getting Andor camera {}, handle {}:\n{}'.format(camnum,self.cameraHandleList[camnum],ERROR_CODE[error]))
                raise PauseError

            error = self.dll.GetCameraSerialNumber(byref(camSerial))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.warning("Initializing camera.".format(camSerial.value))
                error = self.dll.Initialize(".")
                if ERROR_CODE[error] != 'DRV_SUCCESS':
                    logger.error('Error initializing Andor camera in getAllSerials:\n{} ({})'.format(ERROR_CODE[error],error))
                    raise PauseError
                error = self.dll.GetCameraSerialNumber(byref(camSerial))
                if ERROR_CODE[error] != 'DRV_SUCCESS':
                    logger.error('Error getting Andor camera serial number in getAllSerials:\n{} ({})'.format(ERROR_CODE[error],error))
                    raise PauseError
            self.cameraSerialList[camnum] = camSerial.value
            logger.warning("Serial for camera {}: {}".format(camnum,camSerial.value))
        #set up dictionary

        self.cameraHandleDict = dict(zip(self.cameraSerialList,self.cameraHandleList))


    def checkSerial(self):
        camSerial=c_int()
        error = self.dll.GetCameraSerialNumber(byref(camSerial))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error in getAllSerials getting Andor camera serial number:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.CurrentHandle = camSerial.value
        return camSerial.value

    def setCamera(self):
        if not self.isInitialized:
            self.initialize()
        if self.cameraHandleDict is None:
            self.getAllSerials()

        try:
            error = self.dll.SetCurrentCamera(self.cameraHandleDict[self.currentCamera.value])
        except Exception as e:
            logger.error("Invalid camera number: {}. Exception: {}".format(self.cameraHandleDict[self.currentCamera.value],e))
            raise PauseError
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error setting current camera:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        currentCam = c_long()
        error = self.dll.GetCurrentCamera(byref(currentCam))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error setting current camera:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        #logger.warning("GetCurrentCamera says current camera Handle is: {}".format(currentCam.value))

        camSerial=c_int()
        error = self.dll.GetCameraSerialNumber(byref(camSerial))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.warning("Initializing camera.")
            error = self.dll.Initialize(".")
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error initializing Andor camera:\n{} ({})'.format(ERROR_CODE[error],error))
                raise PauseError

        self.checkSerial()
        self.GetTemperature()


    def GetNumberNewImages(self, dump=False):
        first = c_long()
        last = c_long()
        error = self.dll.GetNumberNewImages(byref(first), byref(last))
        if not dump:
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error in GetNumberNewImages:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            n = (last.value-first.value)
            if n != self.shotsPerMeasurement.value:
                logger.warning('Andor camera acquired {} images, but was expecting {}.'.format(n, self.shotsPerMeasurement.value))
                raise PauseError
        return first.value, last.value

    def GetImages(self):
        if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == self.experiment.measurementsPerIteration - 1)):
            self.setCamera()
            #print "Waiting for acquisition"
            self.WaitForAcquisition()
            #print "calling GetAcquiredData"
            data = self.GetAcquiredData()
            #self.StartAcquisition()
            return data
        return 0

    def setROIvalues(self):
        if self.ROI is None:
            self.setCamera()
            self.GetDetector()

        self.ROI[2] = 1   #x-binning

        self.ROI[0] = min(self.roihighh,self.roilowh)   #x
        self.ROI[1] = max(self.roihighh,self.roilowh)   #width
        self.ROI[3] = min(-1*self.roihighv,-1*self.roilowv)   #x
        self.ROI[4] = max(-1*self.roihighv,-1*self.roilowv)   #width

        self.ROI[5] = 1   #y-binning

        self.width = self.ROI[1] - self.ROI[0]
        self.height = self.ROI[4] - self.ROI[3]
        self.dim = self.width*self.height
        #print "self.width: {} self.height: {}".format(self.width,self.height)
        #print "ROI: {}".format(self.ROI)

    def DumpImages(self):
        self.setCamera()
        #logger.warning("Dumping old images for camera {}".format(self.CurrentHandle))
        while True:
            first, last = self.GetNumberNewImages(dump=True)
            n = (last-first)
            #logger.warning("Dumping {} images".format(n))
            if n==0:
                break
            size = self.dim * n
            c_image_array_type = c_int * size
            c_image_array = c_image_array_type()
            validfirst = c_long()
            validlast = c_long()
            error = self.dll.GetImages(first, last, byref(c_image_array), size, byref(validfirst), byref(validlast))

    def GetDetector(self):
        width = c_int()
        height = c_int()

        error = self.dll.GetDetector(byref(width), byref(height))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error getting Andor camera sensor size:\n{}'.format(ERROR_CODE[error]))
            raise PauseError


        self.width = width.value
        self.height = height.value  # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.dim = self.width * self.height

        self.roimaxv = -self.height
        self.roimaxh = self.width
        #self.width = self.width - 1
        #self.height = self.height - 1   # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.ROI = [0, self.width, 1, 0, self.height, 1 ]
        #print 'Andor: width {}, height {}'.format(self.width, self.height)
        return self.width, self.height

    def DLLError(self, func, error, NoPause=False):
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error in {} on camera {}:\n{}'.format(func,ERROR_CODE[error],self.currentCamera.value))
            if not NoPause:
                raise PauseError
            return False
        return True

    def DLLErrorTemp(self, func, error, NoPause=False):
        if ERROR_CODE[error] != 'DRV_TEMPERATURE_STABILIZED' and ERROR_CODE[error] != 'DRV_TEMPERATURE_NOT_STABILIZED':
            logger.error('Error in {}:\n{}'.format(func,ERROR_CODE[error]))
            if not NoPause:
                raise PauseError
            return False
        return True


    def AbortAcquisition(self):
        error = self.dll.AbortAcquisition()
        self.DLLError(sys._getframe().f_code.co_name, error)

    def ShutDown(self):
        error = self.dll.ShutDown()
        self.DLLError(sys._getframe().f_code.co_name, error, True)

    def GetCameraSerialNumber(self):
        serial = c_int()
        error = self.dll.GetCameraSerialNumber(byref(serial))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.serial = serial.value
        return self.serial

    def SetReadMode(self, mode):
        error = self.dll.SetReadMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetAcquisitionMode(self, mode):
        error = self.dll.SetAcquisitionMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetNumberKinetics(self, number):
        error = self.dll.SetNumberKinetics(number)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetNumberAccumulations(self, number):
        error = self.dll.SetNumberAccumulations(number)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetAccumulationCycleTime(self, time):
        error = self.dll.SetAccumulationCycleTime(c_float(time))
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetKineticCycleTime(self, time):
        error = self.dll.SetKineticCycleTime(c_float(time))
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetShutter(self, typ, mode, closingtime, openingtime):
        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetImage(self, hbin, vbin, hstart, hend, vstart, vend):
        error = self.dll.SetImage(hbin, vbin, hstart, hend, vstart, vend)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def StartAcquisition(self):
        self.setCamera()
        error = self.dll.StartAcquisition()
        if (ERROR_CODE[error] == 'DRV_ACQUIRING'):
            logger.error("Acquisition in process... is camera assigned twice?")
        self.DLLError(sys._getframe().f_code.co_name, error)

    def WaitForAcquisition(self):
        self.setCamera()
        error = self.dll.WaitForAcquisition()
        self.DLLError(sys._getframe().f_code.co_name, error)
    
    def GetAcquiredData(self, dump=False):
        #print "declaring c_image_array"
        c_image_array_type = c_int * self.dim * self.shotsPerMeasurement.value
        c_image_array = c_image_array_type()
        #print "calling dll"
        error = self.dll.GetAcquiredData(byref(c_image_array), self.dim * self.shotsPerMeasurement.value)
        self.DLLError(sys._getframe().f_code.co_name, error, dump)

        data = numpy.ctypeslib.as_array(c_image_array)
        data = numpy.reshape(data, (self.shotsPerMeasurement.value, self.height, self.width))
        return data

    def CreateAcquisitionBuffer(self):
        """This function creates an image buffer to be used for video display.
        The buffer will be updated by the GetMostRecentImage method, to give the fastest
        possible update.  A numpy array that uses the same memory space as the c array is returned.
        That way plotting functions like matplotlib can be used and the plot data can be
        automatically updated whenever new data is available.  All that needs to be done is for the
        plot to be redrawn whenever a new image is captured."""

        try:
            c_image_array_type = c_int * self.dim
            self.c_image_array = c_image_array_type()

            data = numpy.ctypeslib.as_array(self.c_image_array)
            data = numpy.reshape(data, (self.height, self.width))
        except Exception as e:
            logger.error("Exception in CreateAcquisitionBuffer: {}".format(e))
            logger.error("dim={} height={} width={}".format(self.dim,self.height,self.width))
            logger.error("data shape: {}".format(data.shape))
            raise PauseError
        self.data = data
        return data

    def GetMostRecentImage(self):
        self.setCamera()
        """This function gets the most recent image, for video display.
        It must be preceded by a call to CreateAcquisitionBuffer() and StartAcquisition().
        The image data is put into self.c_image_array, which must already be allocated (by Create AcquisitionBuffer)."""

        error = self.dll.GetMostRecentImage(byref(self.c_image_array), self.dim)
        return self.DLLError(sys._getframe().f_code.co_name, error, True)

    def SetExposureTime(self, time):
        self.setCamera()
        error = self.dll.SetExposureTime(c_float(time/1000.0))
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def GetAcquisitionTimings(self):
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        error = self.dll.GetAcquisitionTimings(byref(exposure), byref(accumulate), byref(kinetic))
        self.DLLError(sys._getframe().f_code.co_name, error)

        #self.exposure = exposure.value
        #self.accumulate = accumulate.value
        #self.kinetic = kinetic.value

        return exposure.value, accumulate.value, kinetic.value

    def SetCoolerMode(self, mode):
        error = self.dll.SetCoolerMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetImageRotate(self, iRotate):
        error = self.dll.SetImageRotate(iRotate)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetImageFlip(self, iHFlip, iVFlip):
        error = self.dll.SetImageFlip(iHFlip, iVFlip)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SaveAsFITS(self, filename, typ):
        error = self.dll.SaveAsFITS(filename, typ)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def CoolerON(self):
        error = self.dll.CoolerON()
        self.DLLError(sys._getframe().f_code.co_name, error)

    def CoolerOFF(self):
        error = self.dll.CoolerOFF()
        self.DLLError(sys._getframe().f_code.co_name, error)

    def IsCoolerOn(self):
        iCoolerStatus = c_int()
        error = self.dll.IsCoolerOn(byref(iCoolerStatus))
        self.DLLError(sys._getframe().f_code.co_name, error)
        if iCoolerStatus.value == 0:
            return False
        else:
            return True

    def GetTemperature(self):
        ctemperature = c_float()
        error = self.dll.GetTemperatureF(byref(ctemperature))
        self.DLLErrorTemp(sys._getframe().f_code.co_name, error, True)
        self.temperature = ctemperature.value
        return self.temperature

    def SetTemperature(self, temperature):
        error = self.dll.SetTemperature(temperature)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.set_T = temperature

    def GetEMCCDGain(self):
        gain = c_int()
        error = self.dll.GetEMCCDGain(byref(gain))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.gain = gain.value
        return gain.value

    def SetEMGainMode(self, mode):
        error = self.dll.SetEMGainMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetEMCCDGain(self, gain):
        error = self.dll.SetEMCCDGain(gain)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetEMAdvanced(self, state):
        error = self.dll.SetEMAdvanced(state)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def GetEMGainRange(self):
        low = c_int()
        high = c_int()
        error = self.dll.GetEMGainRange(byref(low), byref(high))
        gain_range = (low.value, high.value)
        self.DLLError(sys._getframe().f_code.co_name, error)
        return gain_range

    def GetNumberADChannels(self):
        number_AD_channels = c_int()
        error = self.dll.GetNumberADChannels(byref(number_AD_channels))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.number_AD_channels = number_AD_channels.value

    def GetBitDepth(self):
        bit_depth = c_int()
        self.bit_depths = []

        for i in range(self.number_AD_channels):
            error = self.dll.GetBitDepth(i, byref(bit_depth))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.bit_depths.append(bit_depth.value)

    def SetADChannel(self, index):
        error = self.dll.SetADChannel(index)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.channel = index

    def SetOutputAmplifier(self, typ):
        error = self.dll.SetOutputAmplifier(typ)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.outamp = typ

    def GetNumberHSSpeeds(self):
        noHSSpeeds = c_int()
        error = self.dll.GetNumberHSSpeeds(self.channel, self.outamp, byref(noHSSpeeds))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.noHSSpeeds = noHSSpeeds.value

    def GetHSSpeed(self):
        HSSpeed = c_float()
        self.HSSpeeds = []

        for i in range(self.noHSSpeeds):
            error = self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.HSSpeeds.append(HSSpeed.value)
            
    def SetHSSpeed(self, index):
        error = self.dll.SetHSSpeed(index)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.HSSpeed = index

    def GetNumberVSSpeeds(self):
        noVSSpeeds = c_int()
        error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.noVSSpeeds = noVSSpeeds.value

    def GetVSSpeed(self):
        VSSpeed = c_float()
        self.VSSpeeds = []

        for i in range(self.noVSSpeeds):
            error = self.dll.GetVSSpeed(i, byref(VSSpeed))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.VSSpeeds.append(VSSpeed.value)

    def SetVSSpeed(self, index):
        error = self.dll.SetVSSpeed(index)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.VSSpeed = index

    def GetNumberPreAmpGains(self):
        noGains = c_int()
        error = self.dll.GetNumberPreAmpGains(byref(noGains))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.noGains = noGains.value

    def GetPreAmpGain(self):
        gain = c_float()
        self.preAmpGains = []

        for i in range(self.noGains):
            self.dll.GetPreAmpGain(i, byref(gain))
            self.preAmpGains.append(gain.value)

    def SetPreAmpGain(self, index):
        error = self.dll.SetPreAmpGain(index)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetTriggerMode(self, mode):
        error = self.dll.SetTriggerMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def GetStatus(self):
        status = c_int()
        error = self.dll.GetStatus(byref(status))
        self.DLLError(sys._getframe().f_code.co_name, error, True)
        self.status = ERROR_CODE[status.value]
        return self.status

    def GetAcquisitionProgress(self):
        acc = c_long()
        series = c_long()
        error = self.dll.GetAcquisitionProgress(byref(acc), byref(series))
        self.DLLError(sys._getframe().f_code.co_name, error)
        return acc.value, series.value

    def SetFrameTransferMode(self, frameTransfer):
        error = self.dll.SetFrameTransferMode(frameTransfer)
        self.DLLError(sys._getframe().f_code.co_name, error)
        
    def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
        error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetSpool(self, active, method, path, framebuffersize):
        error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
        self.DLLError(sys._getframe().f_code.co_name, error)

ERROR_CODE = {
    20001: "DRV_ERROR_CODES",
    20002: "DRV_SUCCESS",
    20003: "DRV_VXDNOTINSTALLED",
    20004: "DRV_ERROR_SCAN",
    20005: "DRV_ERROR_CHECK_SUM",
    20006: "DRV_ERROR_FILELOAD",
    20007: "DRV_UNKNOWN_FUNCTION",
    20008: "DRV_ERROR_VXD_INIT",
    20009: "DRV_ERROR_ADDRESS",
    20010: "DRV_ERROR_PAGELOCK",
    20011: "DRV_ERROR_PAGE_UNLOCK",
    20012: "DRV_ERROR_BOARDTEST",
    20013: "DRV_ERROR_ACK",
    20014: "DRV_ERROR_UP_FIFO",
    20015: "DRV_ERROR_PATTERN",
    20017: "DRV_ACQUISITION_ERRORS",
    20018: "DRV_ACQ_BUFFER",
    20019: "DRV_ACQ_DOWNFIFO_FULL",
    20020: "DRV_PROC_UNKNOWN_INSTRUCTION",
    20021: "DRV_ILLEGAL_OP_CODE",
    20022: "DRV_KINETIC_TIME_NOT_MET",
    20023: "DRV_ACCUM_TIME_NOT_MET",
    20024: "DRV_NO_NEW_DATA",
    20026: "DRV_SPOOLERROR",
    20027: "DRV_SPOOLSETUPERROR",
    20033: "DRV_TEMPERATURE_CODES",
    20034: "DRV_TEMPERATURE_OFF",
    20035: "DRV_TEMP_NOT_STABILIZED",
    20036: "DRV_TEMPERATURE_STABILIZED",
    20037: "DRV_TEMPERATURE_NOT_REACHED",
    20038: "DRV_TEMPERATURE_OUT_RANGE",
    20039: "DRV_TEMPERATURE_NOT_SUPPORTED",
    20040: "DRV_TEMPERATURE_DRIFT",
    20049: "DRV_GENERAL_ERRORS",
    20050: "DRV_INVALID_AUX",
    20051: "DRV_COF_NOTLOADED",
    20052: "DRV_FPGAPROG",
    20053: "DRV_FLEXERROR",
    20054: "DRV_GPIBERROR",
    20064: "DRV_DATATYPE",
    20065: "DRV_DRIVER_ERRORS",
    20066: "DRV_P1INVALID",
    20067: "DRV_P2INVALID",
    20068: "DRV_P3INVALID",
    20069: "DRV_P4INVALID",
    20070: "DRV_INIERROR",
    20071: "DRV_COFERROR",
    20072: "DRV_ACQUIRING",
    20073: "DRV_IDLE",
    20074: "DRV_TEMPCYCLE",
    20075: "DRV_NOT_INITIALIZED",
    20076: "DRV_P5INVALID",
    20077: "DRV_P6INVALID",
    20078: "DRV_INVALID_MODE",
    20079: "DRV_INVALID_FILTER",
    20080: "DRV_I2CERRORS",
    20081: "DRV_DRV_I2CDEVNOTFOUND",
    20082: "DRV_I2CTIMEOUT",
    20083: "DRV_P7INVALID",
    20089: "DRV_USBERROR",
    20090: "DRV_IOCERROR",
    20091: "DRV_VRMVERSIONERROR",
    20093: "DRV_USB_INTERRUPT_ENDPOINT_ERROR",
    20094: "DRV_RANDOM_TRACK_ERROR",
    20095: "DRV_INVALID_TRIGGER_MODE",
    20096: "DRV_LOAD_FIRMWARE_ERROR",
    20097: "DRV_DIVIDE_BY_ZERO_ERROR",
    20098: "DRV_INVALID_RINGEXPOSURES",
    20099: "DRV_BINNING_ERROR",
    20100: "DRV_INVALID_AMPLIFIER",
    20101: "DRV_INVALID_COUNTCONVERT_MODE",
    20115: "DRV_ERROR_MAP",
    20116: "DRV_ERROR_UNMAP",
    20117: "DRV_ERROR_MDL",
    20118: "DRV_ERROR_UNMDL",
    20119: "DRV_ERROR_BUFFSIZE",
    20121: "DRV_ERROR_NOHANDLE",
    20130: "DRV_GATING_NOT_AVAILABLE",
    20131: "DRV_FPGA_VOLTAGE_ERROR",
    20990: "DRV_ERROR_NOCAMERA",
    20991: "DRV_NOT_SUPPORTED",
    20992: "DRV_NOT_AVAILABLE"
}


class AndorViewer(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    shot = Int(0)
    update_lock = Bool(False)
    artist = Member()
    mycam=Member()
    ax = Member()
    bgsub = Bool(False)

    maxPixel = Int(0)
    meanPixel = Int(0)

    def __init__(self, name, experiment, description,camera):
        super(AndorViewer, self).__init__(name, experiment, description)
        self.properties += ['shot', 'bgsub']
        self.mycam=camera

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        #print "analyzeMeasurement: Looking for 'data/Andor_{}'".format(self.mycam.CurrentHandle)
        if 'data/Andor_{}'.format(self.mycam.CurrentHandle) in measurementResults:
            #for each image
            self.data = measurementResults['data/Andor_{}'.format(self.mycam.CurrentHandle)]
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
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
                        mydat = - self.data[1] + self.data[0]
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

                    self.maxPixel = numpy.max(self.data[self.shot])
                    self.meanPixel = int(numpy.mean(self.data[self.shot]))
                super(AndorViewer, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in AndorViewer.updateFigure()\n:{}'.format(e))
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
        super(AndorViewer, self).updateFigure()

    def redraw_video(self):
        """First update self.data using Andor methods, then redraw screen using this."""
        if (self.mycam.autoscale):
            self.artist.autoscale()
        else:
            self.artist.set_data(self.data)
        deferred_call(self.figure.canvas.draw)
        self.maxPixel = numpy.max(self.data[self.shot])              #What does "shot" mean in video mode?
        self.meanPixel = int(numpy.mean(self.data[self.shot]))


class Andor(Instrument):
    camera = Member()
    analysis = Member()

    def __init__(self, name, experiment, description=''):
        super(Andor, self).__init__(name, experiment, description)
        self.camera = AndorCamera('Camera{}'.format(name),experiment,'Andor Camera')
        self.analysis = AndorViewer('Viewer{}'.format(name),experiment,'Andor Viewer',self.camera)
        self.properties += ['camera','analysis']

    def evaluate(self):
        self.camera.evaluate()


class Andors(Instrument,Analysis):
    version = '2016.06.02'
    motors = Member()
    dll = Member()

    def __init__(self, name, experiment, description=''):
        super(Andors, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Andor cameras', listElementType=Andor,
                               listElementName='motor')
        self.properties += ['version', 'motors']
        self.initialize(True)

    def initializecameras(self):
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.initialize()
        except Exception as e:
            logger.error('Problem initializing Andor camera:\n{}\n{}\n'.format(msg,e))
            self.isInitialized = False
            raise PauseError

    def initialize(self, cameras=False):
        msg=''
        try:
            self.dll = CDLL(r"D:\git\cspycontroller\python\Andor\atmcd64d.dll")
        except Exception as e:
            logger.warning('Failed to load DLL for Andor (check path?): {}. Andor disabled.'.format(e))
            self.enable = False
            return
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
            logger.error('Problem starting Andor camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

        self.isDone = True




    def update(self):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    #logger.warning( "Updating camera {}".format(i.camera.CurrentHandle))
                    msg = i.camera.update()
        except Exception as e:
            logger.error('Problem updating Andor camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def evaluate(self):
        msg = ''
        try:
            for i in self.motors:
                msg = i.evaluate()
        except Exception as e:
            logger.error('Problem evaluating Andor camera:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def writeResults(self, hdf5):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    msg = i.camera.writeResults(hdf5)
        except Exception as e:
            logger.error('Problem writing Andor camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def acquire_data(self):
        msg = ''
        try:
            for i in self.motors:
                if i.camera.enable:
                    logger.debug( "Acquiring data from camera {}".format(i.camera.CurrentHandle))
                    msg = i.camera.acquire_data()
        except Exception as e:
            logger.error('Problem acquiring Andor camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def __del__(self):
        if self.isInitialized:
            for i in self.motors:
                try:
                    if i.camera.GetStatus() == 'DRV_ACQUIRING':
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
                    logger.debug("Displaying data from camera {}".format(i.camera.CurrentHandle))
                    msg = i.analysis.analyzeMeasurement(measurementresults,iterationresults,hdf5)
        except Exception as e:
            logger.error('Problem displaying Andor camera data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError
        return 0

