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
import os
import numpy
from atom.api import Int, Tuple, List, Str, Float, Bool, Member, observe
from instrument_property import IntProp, FloatProp
from cs_instruments import Instrument

# imports for viewer
from analysis import AnalysisWithFigure
from colors import my_cmap

class Andor(Instrument):

    EMCCDGain = Member()
    preAmpGain = Member()
    exposureTime = Member()
    triggerMode = Int()
    shotsPerMeasurement = Member()

    width = Int()  # the number of columns
    height = Int()  # the number of rows
    dim = Int()  # the total number of pixels
    serial = Int()  # the serial number of the camera
    c_image_array = Member()  # a c_int array to store incoming image data
    set_T = Int()
    temperature = Int()
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

    data = Member()  # holds acquired images until they are written

    def __init__(self, name, experiment, description=''):
        super(Andor, self).__init__(name, experiment, description)
        self.EMCCDGain = IntProp('EMCCDGain', experiment, 'Andor EM gain', '0')
        self.preAmpGain = IntProp('preAmpGain', experiment, 'Andor analog gain', '0')
        self.exposureTime = FloatProp('exposureTime', experiment, 'exposure time for edge trigger', '0')
        self.shotsPerMeasurement = IntProp('shotsPerMeasurement', experiment, 'number of expected shots', '0')
        self.properties += ['EMCCDGain', 'preAmpGain', 'exposureTime', 'triggerMode']

    def __del__(self):
        if self.isInitialized:
            self.ShutDown()

    def initialize(self):
        """Starts the dll and finds the camera."""

        self.InitializeCamera()
        self.GetCameraSerialNumber()
        self.SetCoolerMode(1)
        self.CoolerON()

        self.isInitialized = True

    def update(self):
        if self.GetStatus() == 'DRV_ACQUIRING':
            self.AbortAcquisition()
        self.SetPreAmpGain(self.preAmpGain.value)
        self.SetEMCCDGain(self.EMCCDGain.value)
        self.SetExposureTime(self.exposureTime.value)
        if self.triggerMode == 0:
            # set edge trigger
            self.SetTriggerMode(6)
        else:
            # set level trigger
            self.SetTriggerMode(7)
        self.SetReadMode(4)  # image mode
        self.SetImage(1, 1, 1, self.width, 1, self.height)  # full sensor, no binning
        self.SetAcquisitionMode(5)  # run till abort
        self.SetKineticCycleTime(0)  # no delay
        self.StartAcquisition()

    def acquire_data(self):
        self.data = self.GetImages()

    def writeResults(self, hdf5):
        """Write the obtained images to hdf5 file"""
        try:
            hdf5['Andor'] = self.data
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
        self.dll = CDLL(os.path.join("andor", "atmcd64d.dll"))
        error = self.dll.Initialize(".")
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error initializing Andor camera:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def GetNumberNewImages(self):
        first = c_long()
        last = c_long()
        error = self.dll.GetNumberNewImages(byref(first), byref(last))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        n = (last-first)
        if n != self.shotsPerMeasurement.value:
            logger.warning('Andor camera acquired {} images, but was expecting {}.'.format(n, self.shotsPerMeasurement))
            raise PauseError
        return first.value, last.value

    def GetImages(self):
        first, last = self.GetNumberNewImages()
        n = (last-first)
        size = self.dim * n
        c_image_array_type = c_int * size
        c_image_array = c_image_array_type()
        validfirst = c_long()
        validlast = c_long()
        error = self.dll.GetImages(first, last, c_image_array, size, validfirst, validlast)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error in Andor.GetImages:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        else:
            data = numpy.ctypeslib.as_array(self.cimage)
            data = numpy.reshape(data, (n, self.width, self.height))
            return data

    def GetDetector(self):
        width = c_int()
        height = c_int()

        error = self.dll.GetDetector(byref(width), byref(height))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error getting Andor camera sensor size:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

        self.width = width.value
        self.height = height.value - 2  # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.dim = self.width * self.height

        return self.width, self.value

    def AbortAcquisition(self):
        error = self.dll.AbortAcquisition()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def ShutDown(self):
        error = self.dll.ShutDown()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))

    def GetCameraSerialNumber(self):
        serial = c_int()
        error = self.dll.GetCameraSerialNumber(byref(serial))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.serial = serial.value
        return self.serial

    def SetReadMode(self, mode):
        error = self.dll.SetReadMode(mode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetAcquisitionMode(self, mode):
        error = self.dll.SetAcquisitionMode(mode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetNumberKinetics(self, number):
        error = self.dll.SetNumberKinetics(number)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetNumberAccumulations(self, number):
        error = self.dll.SetNumberAccumulations(number)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetAccumulationCycleTime(self, time):
        error = self.dll.SetAccumulationCycleTime(c_float(time))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetKineticCycleTime(self, time):
        error = self.dll.SetKineticCycleTime(c_float(time))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetShutter(self, typ, mode, closingtime, openingtime):
        error = self.dll.SetShutter(typ, mode, closingtime, openingtime)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetImage(self, hbin, vbin, hstart, hend, vstart, vend):
        error = self.dll.SetImage(hbin, vbin, hstart, hend, vstart, vend)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def StartAcquisition(self):
        error = self.dll.StartAcquisition()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def WaitForAcquisition(self):
        error = self.dll.WaitForAcquisition()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
    
    def GetAcquiredData(self):
        c_image_array_type = c_int * self.dim
        c_image_array = c_image_array_type()
        error = self.dll.GetAcquiredData(byref(c_image_array), self.dim)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        else:
            data = numpy.ctypeslib.as_array(self.cimage)
            data = numpy.reshape(data, (self.width, self.height))
            return data

    def CreateAcquisitionBuffer(self):
        """This function creates an image buffer to be used for video display.
        The buffer will be updated by the GetMostRecentImage method, to give the fastest
        possible update.  A numpy array that uses the same memory space as the c array is returned.
        That way plotting functions like matplotlib can be used and the plot data can be
        automatically updated whenever new data is available.  All that needs to be done is for the
        plot to be redrawn whenever a new image is captured."""

        c_image_array_type = c_int * self.dim
        self.c_image_array = c_image_array_type()

        data = numpy.ctypeslib.as_array(self.cimage)
        data = numpy.reshape(data, (self.width, self.height))
        return data

    def GetMostRecentImage(self):
        """This function gets the most recent image, for video display.
        It must be preceded by a call to CreateAcquisitionBuffer() and StartAcquisition().
        The image data is put into self.cimage, which must already be allocated (by Create AcquisitionBuffer)."""

        error = self.dll.GetMostRecentImage(byref(self.c_image_array), self.dim)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetExposureTime(self, time):
        error = self.dll.SetExposureTime(c_float(time))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def GetAcquisitionTimings(self):
        exposure = c_float()
        accumulate = c_float()
        kinetic = c_float()
        error = self.dll.GetAcquisitionTimings(byref(exposure), byref(accumulate), byref(kinetic))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

        self.exposure = exposure.value
        self.accumulate = accumulate.value
        self.kinetic = kinetic.value

        return self.exposure, self.accumulate, self.kinetic

    def SetCoolerMode(self, mode):
        error = self.dll.SetCoolerMode(mode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetImageRotate(self, iRotate):
        error = self.dll.SetImageRotate(iRotate)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SaveAsFITS(self, filename, typ):
        error = self.dll.SaveAsFITS(filename, typ)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def CoolerON(self):
        error = self.dll.CoolerON()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def CoolerOFF(self):
        error = self.dll.CoolerOFF()
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def IsCoolerOn(self):
        iCoolerStatus = c_int()
        error = self.dll.IsCoolerOn(byref(iCoolerStatus))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        if iCoolerStatus.value == 0:
            return False
        else:
            return True

    def GetTemperature(self):
        ctemperature = c_int()
        error = self.dll.GetTemperature(byref(ctemperature))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.temperature = ctemperature.value
        return self.temperature

    def SetTemperature(self, temperature):
        error = self.dll.SetTemperature(temperature)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.set_T = temperature

    def GetEMCCDGain(self):
        gain = c_int()
        error = self.dll.GetEMCCDGain(byref(gain))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.gain = gain.value

    def SetEMGainMode(self, mode):
        error = self.dll.SetEMGainMode(mode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetEMCCDGain(self, gain):
        error = self.dll.SetEMCCDGain(gain)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetEMAdvanced(self, state):
        error = self.dll.SetEMAdvanced(state)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def GetEMGainRange(self):
        low = c_int()
        high = c_int()
        error = self.dll.GetEMGainRange(byref(low), byref(high))
        self.gain_range = (low.value, high.value)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def GetNumberADChannels(self):
        number_AD_channels = c_int()
        error = self.dll.GetNumberADChannels(byref(number_AD_channels))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.number_AD_channels = number_AD_channels.value

    def GetBitDepth(self):
        bit_depth = c_int()
        self.bit_depths = []

        for i in range(self.number_AD_channels):
            error = self.dll.GetBitDepth(i, byref(bit_depth))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            self.bit_depths.append(bit_depth.value)

    def SetADChannel(self, index):
        error = self.dll.SetADChannel(index)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.channel = index

    def SetOutputAmplifier(self, typ):
        error = self.dll.SetOutputAmplifier(typ)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.outamp = typ

    def GetNumberHSSpeeds(self):
        noHSSpeeds = c_int()
        error = self.dll.GetNumberHSSpeeds(self.channel, self.outamp, byref(noHSSpeeds))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.noHSSpeeds = noHSSpeeds.value

    def GetHSSpeed(self):
        HSSpeed = c_float()
        self.HSSpeeds = []

        for i in range(self.noHSSpeeds):
            error = self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            self.HSSpeeds.append(HSSpeed.value)
            
    def SetHSSpeed(self, index):
        error = self.dll.SetHSSpeed(index)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.HSSpeed = index

    def GetNumberVSSpeeds(self):
        noVSSpeeds = c_int()
        error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.noVSSpeeds = noVSSpeeds.value

    def GetVSSpeed(self):
        VSSpeed = c_float()
        self.VSSpeeds = []

        for i in range(self.noVSSpeeds):
            error = self.dll.GetVSSpeed(i, byref(VSSpeed))
            if ERROR_CODE[error] != 'DRV_SUCCESS':
                logger.error('Error:\n{}'.format(ERROR_CODE[error]))
                raise PauseError
            self.VSSpeeds.append(VSSpeed.value)

    def SetVSSpeed(self, index):
        error = self.dll.SetVSSpeed(index)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.VSSpeed = index

    def GetNumberPreAmpGains(self):
        noGains = c_int()
        error = self.dll.GetNumberPreAmpGains(byref(noGains))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.noGains = noGains.value

    def GetPreAmpGain(self):
        gain = c_float()
        self.preAmpGains = []

        for i in range(self.noGains):
            self.dll.GetPreAmpGain(i, byref(gain))
            self.preAmpGains.append(gain.value)

    def SetPreAmpGain(self, index):
        error = self.dll.SetPreAmpGain(index)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetTriggerMode(self, mode):
        error = self.dll.SetTriggerMode(mode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def GetStatus(self):
        status = c_int()
        error = self.dll.GetStatus(byref(status))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        self.status = ERROR_CODE[status.value]
        return self.status

    def GetAcquisitionProgress(self):
        acc = c_long()
        series = c_long()
        error = self.dll.GetAcquisitionProgress(byref(acc), byref(series))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        return acc.value, series.value

    def SetFrameTransferMode(self, frameTransfer):
        error = self.dll.SetFrameTransferMode(frameTransfer)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError
        
    def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
        error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def SetSpool(self, active, method, path, framebuffersize):
        error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

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

    def __init__(self, name, experiment, description=''):
        super(AndorViewer, self).__init__(name, experiment, description)
        self.properties += ['shot']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        if 'data/Andor' in measurementResults:
            #for each image
            self.data = measurementResults['data/Andor']
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock:
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if (self.data is not None) and (self.shot < len(self.data)):
                    ax = fig.add_subplot(111)
                    ax.matshow(self.data[self.shot], cmap=my_cmap)
                    ax.set_title('most recent shot '+str(self.shot))
                super(AndorViewer, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in AndorViewer.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False
