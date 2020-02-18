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
 # test
   # This code is written for Ixon. Will support other Andor cameras in the future.
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

from ctypes import CDLL, c_int, c_float, c_long, c_char_p, byref, windll
import sys, threading, time
import numpy
from atom.api import Int, Tuple, List, Str, Float, Bool, Member, observe
from instrument_property import IntProp, FloatProp, ListProp
from cs_instruments import Instrument

# imports for viewer
from analysis import AnalysisWithFigure, Analysis
from colors import my_cmap
from enaml.application import deferred_call

import ConfigParser


def intialize_numpy_array(array, default):
    '''Helper for initializing a numpy array.
    Returns tuple of (changed, array).
    if array exists then changed=False and array=array
    if array doesn't exist then changed=True and array=default
    '''
    try:
        _ = array.shape
    except (AttributeError, NameError):
        return (True, default)
    return (False, array)


class AndorCamera(Instrument):

    EMCCDGain = Member()
    exposureTime = Member()
    triggerMode = Int()
    acquisitionMode = Int()
    AdvancedEMGain = Int()
    EMGainMode = Int()
    binMode = Int(0)
    shotsPerMeasurement = Member()
    width = Int()  # the number of columns after binning
    height = Int()  # the number of rows after binning
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
    HSIndex = Int()  # Setpoint, read from cfg
    HSSpeeds = List()
    HSSpeed = Member()  # Actual index that the camera sees
    noVSSpeeds = Int()  # total number of supported speeds
    VSIndex = Int()  # Setpoint, read from cfg
    VSSpeeds = List()  # A list of VS speeds.
    VSSpeed = Member()  # Actual number (float) of the speed.
    noGains = Int()
    preAmpGains = List()
    preAmpGain = Member()  # Actual number
    preAmpGainIndex = Int()  # Setpoint, read from cfg
    status = Str()
    accumulate = Float()
    kinetic = Float()

    num_cameras = c_long()
    cameraHandleList = Member()
    cameraHandleDict = Member()
    cameraSerialList = Member()

    CurrentHandle = Int()

    data = Member()  # holds acquired images until they are written
    mode = Str('experiment')  # experiment vs. video
    analysis = Member()  # holds a link to the GUI display
    dll = Member()

    # size of CCD, width and height can change depending on binning
    ccd_size = Member()
    subimage_position = Member()  # position of subimage corner (H,V)
    subimage_size = Member()  # size of subimage

    ROI = Member()
    enableROI = True  # activates slider

    autoscale = Bool(True)
    minPlot = Member()
    maxPlot = Member()

    # 6: edge trigger, 7: level trigger, 1: external, 0: internal
    triggerChoices = (6, 7, 1, 0)
    # 1 : Single Scan, 2 : Accumulate, 3 : Kinetics, 4 : Fast Kinetics,
    # 5 : Run till abort
    acquisitionChoices = (1, 2, 3, 4, 5)
    binChoices = (1, 2, 4)

    def __init__(self, name, experiment, description=''):
        super(AndorCamera, self).__init__(name, experiment, description)
        self.EMCCDGain = IntProp('EMCCDGain', experiment, 'Andor EM gain', '0')
        self.preAmpGain = IntProp('preAmpGain', experiment, 'Andor analog gain', '0')
        self.exposureTime = FloatProp('exposureTime', experiment, 'exposure time for edge trigger', '0')
        self.shotsPerMeasurement = IntProp('shotsPerMeasurement', experiment, 'number of expected shots', '0')
        self.serial = 0
        self.minPlot = IntProp('minPlot', experiment, 'Minimum Plot Scale Value', '0')
        self.maxPlot = IntProp('maxPlot', experiment, 'Maximum Plot Scale Value', '32768')
        self.VSSpeed = IntProp('VSSpeed', experiment, 'Index for Vertical Shift', '0')
        self.HSSpeed = IntProp('HSSpeed', experiment, 'Index for Horizontal Shift', '0')
        self.subimage_position = [0, 0]
        self.subimage_size = [1, 1]
        self.ccd_size = [1, 1]
        self.width = 1
        self.height = 1
        self.properties += [
            'EMCCDGain', 'preAmpGain', 'exposureTime', 'triggerMode',
            'shotsPerMeasurement', 'minPlot', 'maxPlot', 'VSSpeed', 'HSSpeed',
            'acquisitionMode', 'binMode', 'AdvancedEMGain', 'EMGainMode',
            'ROI', 'set_T', 'serial', 'subimage_position', 'subimage_size'
        ]

    def __del__(self):
        if self.isInitialized:
            self.ShutDown()

    def initialize(self):
        """Starts the dll and finds the camera."""

        self.InitializeCamera()
        self.GetCameraSerialNumber()
        self.SetCoolerMode(1)
        self.CoolerON()
        try:  # the Luca throws a DLL error when attempting to set the temperature.
            self.SetTemperature(self.getTemperatureSP())
        except PauseError:
            logger.warning(
                "Problem setting temperature for camera with serial no: %d",
                self.serial
            )
        self.dll.SetFanMode(0)
        self.setCamera()
        self.GetandSetHSVSPreamp()
        # for some reason the first get detector doesnt seem to work unless I have run set image first
        # MFE 5/2017
        for i in range(2):
            self.GetDetector()
            self.setROIvalues()
        self.rundiagnostics()
        # time.sleep(1)
        self.isInitialized = True

    def start(self):

        # if(self.acquisitionChoices[self.acquisitionMode]==5):
        #     self.CoolerON()
        #     if self.GetStatus() != 'DRV_ACQUIRING':
        #         self.setCamera()
        #         self.StartAcquisition()
        #     self.isDone = True
        #     # Runs when the camera is not in accumulate mode, or even in the mode accumulation count is 0.
        # elif (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == 0)):
        if(self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == 0)):
            self.setCamera()
            if self.GetStatus() == 'DRV_ACQUIRING':
                    self.GetAcquiredData(True)
                    self.AbortAcquisition()
            self.CoolerON()
            self.StartAcquisition()
            self.isDone = True
            

    def update(self):
        if self.enable:  # If enable checkbox is checked,
            self.setCamera()  # Set the camera
            # print "Updating Andor camera {}".format(self.CurrentHandle)
            self.mode = 'experiment'  # set the mode to experiment.
            if self.GetStatus() == 'DRV_ACQUIRING':
                # self.GetAcquiredData(True)
                self.AbortAcquisition()
            self.GetDetector()
            if self.GetStatus() != 'DRV_ACQUIRING':  # If camera is not acquiring data, get the temperature
                self.GetTemperature()
            self.SetAcquisitionMode(self.acquisitionChoices[self.acquisitionMode])
            self.SetReadMode(4)  # image mode
            self.SetExposureTime(self.exposureTime.value)
            exposure, accumulate, kinetic = self.GetAcquisitionTimings()

            self.SetTriggerMode(self.triggerChoices[self.triggerMode])

            # set the ROI field
            self.setROIvalues()
            # propagate ROI info to camera
            self.SetImage()

            msg = "done setImage. With binning of {}, new width and height are {}, {}"
            logger.debug(msg.format(self.binChoices[self.binMode], self.width, self.height))

            if (self.acquisitionChoices[self.acquisitionMode]==3 or self.acquisitionChoices[self.acquisitionMode]==4):
                self.SetNumberKinetics(self.shotsPerMeasurement.value)
            if (self.acquisitionChoices[self.acquisitionMode]!=1 and self.acquisitionChoices[self.acquisitionMode]!=4):
                self.SetFrameTransferMode(0)
            if (self.acquisitionChoices[self.acquisitionMode]==2):
                self.SetNumberAccumulations(self.experiment.measurementsPerIteration)
            self.SetKineticCycleTime(0)  # no delay
            self.SetEMGainMode(self.EMGainMode)
            self.SetEMAdvanced(self.AdvancedEMGain)
            self.GetandSetHSVSPreamp()
            self.SetEMCCDGain(self.EMCCDGain.value)
            self.dll.EnableKeepCleans(1)
            self.SetImageFlip(0, 0)
            # these variables aren't used
            # currentgain = self.GetEMCCDGain()
            # gain_range = self.GetEMGainRange()
            # print "EMGainRange: {}".format(gain_range)
            exposure, accumulate, kinetic = self.GetAcquisitionTimings()
            # print "Values returned by GetAcquisitionTimings: exposure: {}, accumulate:{}, kinetic: {}".format(exposure,accumulate,kinetic)
        # else:
        #    print "Andor camera {} is not enabled".format(self.CurrentHandle)

    def setup_video_thread(self, analysis):
        thread = threading.Thread(target=self.setup_video, args=(analysis,))
        # thread.daemon = True
        thread.start()

    def setup_video(self, analysis):
        if self.experiment.status != 'idle':
            logger.warning('Cannot start video mode unless experiment is idle.')
            return
        self.mode = 'video'
        self.analysis = analysis

        previouslyenabled = self.enable
        self.enable = True
        self.experiment.evaluate()
        self.enable = previouslyenabled

        if not self.isInitialized:
            self.initialize()
        self.setCamera()
        if self.GetStatus() == 'DRV_ACQUIRING':
            self.AbortAcquisition()
        self.GetDetector()
        self.SetEMGainMode(self.EMGainMode)
        self.SetEMAdvanced(self.AdvancedEMGain)
        self.GetandSetHSVSPreamp()
        self.SetEMCCDGain(self.EMCCDGain.value)
        self.SetExposureTime(self.exposureTime.value)
        self.SetTriggerMode(0)
        self.SetReadMode(4)  # image mode
        self.CoolerON()
        # print "bin size: {}".format(self.binChoices[self.binMode])

        self.setROIvalues()
        self.SetImage()
        self.SetAcquisitionMode(5)  # run till abort
        self.SetKineticCycleTime(0)  # no delay

        # print self.width, self.height, self.dim
        if self.binChoices[self.binMode] > 1:
            self.width = self.width / self.binChoices[self.binMode]
            self.height = self.height / self.binChoices[self.binMode]
            self.dim = self.width * self.height
        self.data = self.CreateAcquisitionBuffer()
        self.SetImageFlip(0, 0)
        analysis.setup_video(self.data)

        self.StartAcquisition()

        # run the video loop in a new thread
        self.start_video_thread()
        # thread = threading.Thread(target=self.start_video_thread)
        # thread.daemon = True
        # thread.start()

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
        # print "acquire_data is called"
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
                    hdf5['Andor_{}/columns'.format(self.CurrentHandle)] = self.width
                    hdf5['Andor_{}/rows'.format(self.CurrentHandle)] = self.height
                    hdf5['Andor_{}/numShots'.format(self.CurrentHandle)] = self.shotsPerMeasurement.value
                    # self.data size has two dimensional array. T num of shots x (row*column)
                    # We need to reshape into two dim array having row x column, and each shots saved to different node under /shots/
                    for i in numpy.arange(0, self.shotsPerMeasurement.value):
                        array = numpy.array(self.data[i], dtype=numpy.int32)
                        array.resize(int(self.subimage_size[1]), int(self.subimage_size[0]))
                        # self.data # Defines the name of hdf5 node to write the results on.
                        hdf5['Andor_{0}/shots/{1}'.format(self.CurrentHandle, i)] = array
                except Exception as e:
                    logger.error('in Andor.writeResults:\n{}'.format(e))
                    raise PauseError

    def SetSingleScan(self):
        self.SetReadMode(4)
        self.unsetROI()
        self.SetImage()
        self.SetAcquisitionMode(1)
        self.SetTriggerMode(0)

    def SetVideoMode(self):
        self.SetReadMode(4)
        self.unsetROI()
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
        if self.num_cameras.value > 0:
            logger.info("Number of Andor cameras detected: {}".format(self.num_cameras.value))
        else:
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

    def getTemperatureSP(self):
        '''Gets the camera setpoint with the following priority: setting.hdf5 > config.cfg > 0
        If both file reads fail to return a setpoint, the 0 C default setpoint is not written to a settings file
        to prevent propagation of the error without a warning message.
        The config file option is ANDOR.SetTemp_<serial no> with leading zeros removed.
        Returns the setpoint in deg C.
        '''
        if self.set_T:
            logger.info("Using camera setpoint temperature from previous settings file.")
        else:
            cam_temp_option = "SetTemp_{}".format(self.serial)
            logger.info(
                "Using default camera setpoint temperature from config file `ANDOR.%s`.",
                cam_temp_option
            )
            try:
                self.set_T = self.experiment.Config.config.getint('ANDOR', '{}'.format(cam_temp_option))
            except ConfigParser.NoOptionError:
                logger.warning(
                    "No camera temperature and no config file entry found for `ANDOR.%s`, setting temperature to 0 C.",
                    cam_temp_option
                )
                return 0 # dont set set_T so it doesnt get saved and propagated
        return self.set_T


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
                logger.info("Initializing camera.".format(camSerial.value))
                error = self.dll.Initialize(".")
                if ERROR_CODE[error] != 'DRV_SUCCESS':
                    logger.error('Error initializing Andor camera in getAllSerials:\n{} ({})'.format(ERROR_CODE[error],error))
                    raise PauseError
                error = self.dll.GetCameraSerialNumber(byref(camSerial))
                if ERROR_CODE[error] != 'DRV_SUCCESS':
                    logger.error('Error getting Andor camera serial number in getAllSerials:\n{} ({})'.format(ERROR_CODE[error],error))
                    raise PauseError
            self.cameraSerialList[camnum] = camSerial.value
            logger.info("Serial for camera {}: {}".format(camnum,camSerial.value))
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
            error = self.dll.SetCurrentCamera(self.cameraHandleDict[self.serial])
        except Exception as e:
            logger.exception("Invalid camera number: {}.".format(self.cameraHandleDict[self.serial]))
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
        if self.GetStatus() != 'DRV_ACQUIRING':
           self.GetTemperature()
            #self.GetAcquiredData(True)
            #self.AbortAcquisition()

    def GetNumberNewImages(self, dump=False):
        first = c_long()
        last = c_long()
        error = self.dll.GetNumberNewImages(byref(first), byref(last))
        print "first index : {}".format(first.value)
        print "last index : {}".format(last.value)
        if not dump:
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error in GetNumberNewImages:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            n = (last.value-first.value)+1
            if n != self.shotsPerMeasurement.value:
                logger.warning('Andor camera acquired {} images, but was expecting {}.'.format(n, self.shotsPerMeasurement.value))
                raise PauseError
        return first.value, last.value

    def GetImages(self):
        if (self.acquisitionChoices[self.acquisitionMode]!=2 or (self.acquisitionChoices[self.acquisitionMode]==2 and self.experiment.measurement == self.experiment.measurementsPerIteration - 1)):
            self.setCamera()
            self.WaitForAcquisition()
            data = self.GetAcquiredData()
            return data
        return 0

    def setROIvalues(self):
        '''Set the ROI variable to define a subimage'''
        changed, self.ccd_size = intialize_numpy_array(self.ccd_size, numpy.zeros(2, dtype=int))
        if changed or self.ccd_size[0] == 0: # ccd_size does not exist
            self.setCamera()
            self.GetDetector()
        else:
            self.width = self.ccd_size[0]/self.binChoices[self.binMode]
            self.height = self.ccd_size[1]/self.binChoices[self.binMode]
            self.subimage_position = intialize_numpy_array(self.subimage_position, numpy.zeros(2, dtype=int))[1]
            default_size = numpy.subtract(self.ccd_size, self.subimage_position)
            self.subimage_size = intialize_numpy_array(self.subimage_size, default_size)[1]

            # use temporary variables for the binned position and size to not overrite the settings
            sub_pos = [max(self.subimage_position[i]/self.binChoices[self.binMode], 0) for i in range(2)]
            sub_size = [self.subimage_size[i]/self.binChoices[self.binMode] for i in range(2)]
            self.dim = (sub_size[0])*(sub_size[1])
            h_end, v_end = [min(sub_pos[i]+sub_size[i], self.ccd_size[i]) for i in range(2)]
            self.ROI = map(int, [
                sub_pos[0],                     # hstart
                h_end-1,                        # hend
                self.binChoices[self.binMode],  # h pixel binning
                sub_pos[1],                     # vstart
                v_end-1,                        # vend
                self.binChoices[self.binMode],  # v pixel binning
            ])
            logger.debug('ROI: %s', self.ROI)

    def unsetROIvalues(self):
        '''Set the ROI variable to the full image'''
        self.width = self.ccd_size[0]
        self.height = self.ccd_size[1]
        self.subimage_position = numpy.array([0, 0])
        self.subimage_size = self.ccd_size
        self.dim = self.width*self.height
        self.binMode = 0

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

        self.ccd_size = numpy.array([width.value, height.value])
        self.dim = self.width * self.height

        self.ROI = [0, self.width, 1, 0, self.height, 1 ]
        #print 'Andor: width {}, height {}'.format(self.width, self.height)
        return self.width, self.height

    def DLLError(self, func, error, NoPause=False):
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error in {} on camera {}:\n{}'.format(func,self.serial,ERROR_CODE[error]))
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
        if self.GetStatus() == 'DRV_ACQUIRING':
            self.AbortAcquisition()
            logger.error('Shutter control during acquisition. Acquisition aborted')
            self.mode = 'idle' # set the mode to idle.
        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetImage(self):
        hstart, hend, hbin, vstart, vend, vbin = self.ROI
        # andor expects first pixel = 1, python has first pixel = 0
        error = self.dll.SetImage(hbin, vbin, hstart+1, hend+1, vstart+1, vend+1)
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
        c_image_array_type = c_int * self.dim * self.shotsPerMeasurement.value
        c_image_array = c_image_array_type()

        if self.acquisitionChoices[self.acquisitionMode]!=5:
            error = self.dll.GetAcquiredData(byref(c_image_array), self.dim * self.shotsPerMeasurement.value)
            #errct = 100
            #while (ERROR_CODE[error] == 'DRV_ACQUIRING'):
            #    time.sleep(.1)
            #    self.WaitForAcquisition()
            #    error = self.dll.GetAcquiredData(byref(c_image_array), self.dim * self.shotsPerMeasurement.value)
            #print self.dim
            self.DLLError(sys._getframe().f_code.co_name, error, dump)

        elif self.acquisitionChoices[self.acquisitionMode]==5: # If acqusition mode is Run till abort, data must be read from circular buffer. Attempting dll.GetAcquiredData will not run as it is still acquiring.
            first, last = self.GetNumberNewImages(dump)
            validfirst = c_long()
            validlast = c_long()
            size=self.dim * self.shotsPerMeasurement.value
            error = self.dll.GetImages(first, last, byref(c_image_array), size, byref(validfirst), byref(validlast))
            self.DLLError(sys._getframe().f_code.co_name, error, dump)

        data = numpy.ctypeslib.as_array(c_image_array)
        subimg_size = map(int, self.subimage_size)
        data = numpy.reshape(data, (self.shotsPerMeasurement.value, subimg_size[1], subimg_size[0]))
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
            data = numpy.reshape(data, (self.subimage_size[1], self.subimage_size[0]))
        except Exception as e:
            logger.error("Exception in CreateAcquisitionBuffer: {}".format(e))
            logger.error("dim={} height={} width={}".format(self.dim, self.subimage_size[1], self.subimage_size[0]))
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
        self.setCamera() # user enters time in unit of millisecond.
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
        self.temperature = round(ctemperature.value,1) # Rounds the temperature value
        return self.temperature

    def SetTemperature(self, temperature):
        logger.info("Attempting to set camera temperature to %d C", temperature)
        error = self.dll.SetTemperature(temperature)
        self.DLLError(sys._getframe().f_code.co_name, error)
        #self.set_T = temperature

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
        return self.number_AD_channels

    def GetBitDepth(self):
        self.GetNumberADChannels()
        bit_depth = c_int()
        self.bit_depths = []

        for i in range(self.number_AD_channels):
            error = self.dll.GetBitDepth(i, byref(bit_depth))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.bit_depths.append(bit_depth.value)
        return self.bit_depths

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
        return self.noHSSpeeds

    def GetHSSpeed(self):
        self.GetNumberHSSpeeds()
        HSSpeed = c_float()
        self.HSSpeeds = []

        for i in range(self.noHSSpeeds):
            error = self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.HSSpeeds.append(str(round(HSSpeed.value,0))) # Float numbers are rounded then converted to string.
        return self.HSSpeeds

    def SetHSSpeed(self, index):
        #error = self.dll.SetHSSpeed(index)
        error = self.dll.SetHSSpeed(0,index) # According to Andor SDK, first variable sets output amplification. 0 for electron muliplcation/conventional, 1 for conventional/extendeed NIR mode
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.HSSpeed.value = index # update the index if it succesfully updated the setting

    def GetNumberVSSpeeds(self):
        noVSSpeeds = c_int()
        error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.noVSSpeeds = noVSSpeeds.value
        return self.noVSSpeeds

    def GetVSSpeed(self):
        self.GetNumberVSSpeeds()
        VSSpeed = c_float()
        self.VSSpeeds = []

        for i in range(self.noVSSpeeds):
            error = self.dll.GetVSSpeed(i, byref(VSSpeed))
            self.DLLError(sys._getframe().f_code.co_name, error)
            self.VSSpeeds.append(str(round(VSSpeed.value,4))) # Float numbers are rounded then converted to string.
        return self.VSSpeeds

    def SetVSSpeed(self, index):
        error = self.dll.SetVSSpeed(index)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.VSSpeed.value = index # Update VSSpeed once it is set correctly.

    def GetandSetHSVSPreamp(self): # Read config and set Vertical, Horizontal readout rate and preamp gain
        try:
            cam_VS_option = "VSIndex_{}".format(self.serial)
            self.VSIndex = self.experiment.Config.config.getint('ANDOR', '{}'.format(cam_VS_option))
            self.SetVSSpeed(self.VSIndex)
        except ConfigParser.NoOptionError:
                logger.warning(
                    "No Vertical readout shift rate and no config file entry found for `ANDOR.%s`, setting to index 0",
                    cam_VS_option
                )
                self.SetVSSpeed(0)
        try:
            cam_HS_option = "HSIndex_{}".format(self.serial)
            self.HSIndex = self.experiment.Config.config.getint('ANDOR', '{}'.format(cam_HS_option))
            self.SetHSSpeed(self.HSIndex)
        except ConfigParser.NoOptionError:
                logger.warning(
                    "No Horizontal readout shift rate and no config file entry found for `ANDOR.%s`, setting to index 0",
                    cam_HS_option
                )
                self.SetHSSpeed(0)
        try:
            cam_preamp_option = "PreampGainIndex_{}".format(self.serial)
            self.preAmpGainIndex = self.experiment.Config.config.getint('ANDOR', '{}'.format(cam_preamp_option))
            self.SetPreAmpGain(self.preAmpGainIndex)
        except ConfigParser.NoOptionError:
                logger.warning(
                    "No preamp gain and no config file entry found for `ANDOR.%s`, setting to index 0",
                    cam_preamp_option
                )
                self.SetPreAmpGain(0)

    def GetNumberPreAmpGains(self):
        noGains = c_int()
        error = self.dll.GetNumberPreAmpGains(byref(noGains))
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.noGains = noGains.value
        return self.noGains

    def GetPreAmpGain(self):
        self.GetNumberPreAmpGains() # This needs to run first to get noGains variable
        gain = c_float()
        self.preAmpGains = []

        for i in range(self.noGains):
            self.dll.GetPreAmpGain(i, byref(gain))
            self.preAmpGains.append(str(round(gain.value,1))) # Float numbers are rounded then converted to string.
        return self.preAmpGains

    def SetPreAmpGain(self, index):
        error = self.dll.SetPreAmpGain(index)
        self.DLLError(sys._getframe().f_code.co_name, error)
        self.preAmpGain.value=index # Upon succesful set, update the preampgain.value

    def SetTriggerMode(self, mode):
        error = self.dll.SetTriggerMode(mode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def GetTriggerLevelRange(self):
        minimum=c_float()
        maximum=c_float()
        error = self.dll.GetTriggerLevelRange(byref(minimum),byref(maximum))
        self.DLLError(sys._getframe().f_code.co_name, error)
        return minimum, maximum

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
        if self.GetStatus() == 'DRV_ACQUIRING':
            self.AbortAcquisition()
            logger.error('Shutter control during acquisition. Acquisition aborted')
            self.mode = 'idle' # set the mode to idle.
        error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def SetSpool(self, active, method, path, framebuffersize):
        error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
        self.DLLError(sys._getframe().f_code.co_name, error)

    def rundiagnostics(self):
        logger.info( '\n  '.join([
            '%'*40,
            'This camera supports the following settings',
            '%'*40,
            'Supporting ADC channels: {}'.format(self.GetBitDepth()),
            'Supporting Preamp gain: {}'.format(self.GetPreAmpGain()),
            'Supporting Vertical Shift speed: {}'.format(self.GetVSSpeed()),
            'Supporting Horizontal Shift speed: {}'.format(self.GetHSSpeed()),
            'SupportingEMCCD Gain range:{}'.format(self.GetEMGainRange()),
            '%'*40,
            'Currently set to',
            '%'*40,
            'Current EMCCD Gain:{}'.format(self.GetEMCCDGain()),
            'Current Camera Status :{}'.format(self.GetStatus()),
            'Current Horizontal Shift :{}'.format(self.GetHSSpeed()[self.HSSpeed.value]),
            'Current Vertical Shift :{}'.format(self.GetVSSpeed()[self.VSSpeed.value]),
            'Current preamp gain :{}'.format(self.GetPreAmpGain()[self.preAmpGain.value]),
            'Current Camera Temperature :{}'.format(self.GetTemperature()),
            '%'*40,
        ]))

    def fromHDF5(self, hdf):
        logger.info('Reading from camera hdf5 object')
        super(AndorCamera, self).fromHDF5(hdf)



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
        if 'data/Andor_{0}/shots/{1}'.format(self.mycam.CurrentHandle,self.shot) in measurementResults:
            #for each image
            self.data = measurementResults['data/Andor_{0}/shots/{1}'.format(self.mycam.CurrentHandle,self.shot)]
            #print measurementResults['data/Andor_{0}/shots/{1}'.format(self.mycam.CurrentHandle,self.shot)]
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
                        xlimit=numpy.array([0,self.subimage_size[0]-1]) # Defines x limits one the figure.
                        ylimit=numpy.array([0,self.subimage_size[1]-1]) # Defines x limits one the figure.
                        limits = True
                    except:
                        limits = False
                    fig = self.backFigure
                    fig.clf()

                    if (self.data is not None) and (self.shot < self.mycam.shotsPerMeasurement.value):
                        ax = fig.add_subplot(111)
                        self.ax = ax
                        if self.bgsub and self.mycam.shotsPerMeasurement.value>1:
                            mydat = - self.data[1] + self.data[0]
                        else:
                            #mydat = self.data[self.shot]
                            mydat = self.data
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

                        #self.maxPixel = numpy.max(self.data[self.shot])
                        self.maxPixel = numpy.max(self.data)
                        #self.meanPixel = int(numpy.mean(self.data[self.shot]))
                        self.meanPixel = int(numpy.mean(self.data))
                    super(AndorViewer, self).updateFigure()
                except Exception as e:
                    logger.warning('Problem in AndorViewer.updateFigure()\n:{}'.format(e))
                finally:
                    self.update_lock = False

    def setup_video(self, data):
        """Use this method to connect the analysis figure to an array that will
        be rapidly updated in video mode.
        """
        self.data = data
        fig = self.backFigure
        fig.clf()
        ax = fig.add_subplot(111)

        self.artist = ax.imshow(data, vmin=self.mycam.minPlot.value, vmax=self.mycam.maxPlot.value, cmap=my_cmap)
        super(AndorViewer, self).updateFigure()

    def redraw_video(self):
        """First update self.data using Andor methods, then redraw screen using
        this.
        """
        if (self.mycam.autoscale):
            self.artist.set_data(self.data)
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


class Andors(Instrument, Analysis):
    version = '2016.06.02'
    motors = Member()
    dll = Member()

    def __init__(self, name, experiment, description=''):
        super(Andors, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Andor cameras', listElementType=Andor,
                               listElementName='motor')
        self.properties += ['version', 'motors']

    def initializecameras(self):
        try:
            for i in self.motors:
                if i.camera.enable:
                    logger.info('Initializing camera ser. no.: %d', i.camera.serial)
                    msg = i.camera.initialize()
        except Exception as e:
            logger.exception('Problem initializing Andor camera.')
            self.isInitialized = False
            raise PauseError

    def initialize(self, cameras=False):
        msg=''
        try:
            self.dll = CDLL(self.experiment.Config.config.get('ANDOR', 'ATMCD64D_DLL'))
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
            logger.exception('Problem updating Andor camera.')
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
            logger.exception('Problem acquiring Andor camera data.')
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
            handle = self.dll._handle
            del self.dll
            windll.kernel32.FreeLibrary(handle)
        self.isInitialized = False


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

    def fromHDF5(self, hdf):
        super(Andors, self).fromHDF5(hdf)
        try:
            logger.info('Initializing cameras')
            self.initialize(True)
        except:
            logger.exception('Problem initializing camera.')

    def postExperiment(self,experimentresults):
        # We have been unable to figure out why during the postExperiment call
        # the enable is set to False for Andors.  This is a patch (DB & MFE)
        temp_enable = self.enable
        super(Andors,self).postExperiment(experimentresults)
        self.enable = temp_enable
