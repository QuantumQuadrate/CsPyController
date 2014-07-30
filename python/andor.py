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
import sys
import os
import numpy
from atom.api import Int, Member
from cs_instruments import Instrument


class Andor(Instrument):

    width = Int()  # the number of columns
    height = Int()  # the number of rows
    dim = Int()  # the total number of pixels
    serial = Int()  # the serial number of the camera
    cimage = Member()  # a c_int array to store incoming image data

    temperature = None
    set_T       = None
    gain        = None
    gainRange   = None
    status      = None
    preampgain  = None
    channel     = None
    outamp      = None
    hsspeed     = None
    vsspeed     = None
    exposure    = None
    accumulate  = None
    kinetic     = None

    def __del__(self):
        if self.isInitialized:
            self.ShutDown()

    def initialize(self):
        """Starts the dll and finds the camera."""

        self.InitializeCamera()
        self.GetCameraSerialNumber()
        self.isInitialized = True

    def InitializeCamera(self):
        self.dll = CDLL(os.path.join("andor", "atmcd64d.dll"))
        error = self.dll.Initialize(".")
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error initializing Andor camera:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

    def GetDetector(self):
        width = c_int()
        height = c_int()

        error = self.dll.GetDetector(byref(width), byref(height))
        if ERROR_CODE[error] != 'DRV_SUCCESS':
            logger.error('Error getting Andor camera sensor size:\n{}'.format(ERROR_CODE[error]))
            raise PauseError

        self.width = width.value
        self.height = height.value
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
        dim = self.width * self.height
        cimageArray = c_int * dim
        cimage = cimageArray()
        error = self.dll.GetAcquiredData(byref(cimage),dim)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)

        if ERROR_CODE[error] == 'DRV_SUCCESS':
            #copy to numpy array
            imageArray = numpy.array([i for i in cimage])
            imageArray = numpy.reshape(imageArray, (self.width, self.height))
            self.imageArray = imageArray
        else:
            if self.imageArray is not None:
                # there is no new image, use the old one
                imageArray = self.imageArray
            else:
                # there is no old image, use a blank one
                imageArray = numpy.zeros((self.width, self.height))
        return imageArray

    def CreateAcquisitionBuffer(self):
        """This function creates an image buffer to be used for video display.
        The buffer will be updated by the GetMostRecentImage method, to give the fastest
        possible update.  A numpy array that uses the same memory space as the c array is returned.
        That way plotting functions like matplotlib can be used and the plot data can be
        automatically updated whenever new data is available.  All that needs to be done is for the
        plot to be redrawn whenever a new image is captured."""

        self.dim = self.width * self.height
        cimageArray = c_int * self.dim
        self.cimage = cimageArray()

        data = numpy.ctypeslib.as_array(self.cimage)
        data = numpy.reshape(data, (self.width, self.height))
        return data

    def GetMostRecentImage(self):
        """This function gets the most recent image, for video display.
        It must be preceded by a call to CreateAcquisitionBuffer() and StartAcquisition().
        The image data is put into self.cimage, which must already be allocated (by Create AcquisitionBuffer)."""

        error = self.dll.GetMostRecentImage(byref(self.cimage), self.dim)
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

    def SetSingleScan(self):
        self.SetReadMode(4)
        self.SetImage(1, 1, 1, self.width, 1, self.height)
        self.SetAcquisitionMode(1)

    def SetVideoMode(self):
        self.SetReadMode(4)
        self.SetImage(1, 1, 1, self.width, 1, self.height)
        self.SetAcquisitionMode(5)
        self.SetKineticCycleTime(0)  # for run till abort mode
        self.SetTriggerMode(0)  # internal trigger

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
        #ctemperature = c_int(temperature)
        #error = self.dll.SetTemperature(byref(ctemperature))
        error = self.dll.SetTemperature(temperature)
        self.set_T = temperature
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetEMCCDGain(self):
        gain = c_int()
        error = self.dll.GetEMCCDGain(byref(gain))
        self.gain = gain.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
     
    def SetEMCCDGainMode(self, gainMode):
        error = self.dll.SetEMCCDGainMode(gainMode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]   
        
    def SetEMCCDGain(self, gain):
        error = self.dll.SetEMCCDGain(gain)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
        
    def SetEMAdvanced(self, gainAdvanced):
        error = self.dll.SetEMAdvanced(gainAdvanced)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetEMGainRange(self):
        low = c_int()
        high = c_int()
        error = self.dll.GetEMGainRange(byref(low),byref(high))
        self.gainRange = (low.value, high.value)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
      
    def GetNumberADChannels(self):
        noADChannels = c_int()
        error = self.dll.GetNumberADChannels(byref(noADChannels))
        self.noADChannels = noADChannels.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetBitDepth(self):
        bitDepth = c_int()

        self.bitDepths = []

        for i in range(self.noADChannels):
            self.dll.GetBitDepth(i,byref(bitDepth))
            self.bitDepths.append(bitDepth.value)

    def SetADChannel(self, index):
        error = self.dll.SetADChannel(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.channel = index
        return ERROR_CODE[error]  
        
    def SetOutputAmplifier(self, index):
        error = self.dll.SetOutputAmplifier(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.outamp = index
        return ERROR_CODE[error]
        
    def GetNumberHSSpeeds(self):
        noHSSpeeds = c_int()
        error = self.dll.GetNumberHSSpeeds(self.channel, self.outamp, byref(noHSSpeeds))
        self.noHSSpeeds = noHSSpeeds.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetHSSpeed(self):
        HSSpeed = c_float()

        self.HSSpeeds = []

        for i in range(self.noHSSpeeds):
            self.dll.GetHSSpeed(self.channel, self.outamp, i, byref(HSSpeed))
            self.HSSpeeds.append(HSSpeed.value)
            
    def SetHSSpeed(self, index):
        error = self.dll.SetHSSpeed(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.hsspeed = index
        return ERROR_CODE[error]
        
    def GetNumberVSSpeeds(self):
        noVSSpeeds = c_int()
        error = self.dll.GetNumberVSSpeeds(byref(noVSSpeeds))
        self.noVSSpeeds = noVSSpeeds.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetVSSpeed(self):
        VSSpeed = c_float()

        self.VSSpeeds = []

        for i in range(self.noVSSpeeds):
            self.dll.GetVSSpeed(i,byref(VSSpeed))
            self.preVSpeeds.append(VSSpeed.value)

    def SetVSSpeed(self, index):
        error = self.dll.SetVSSpeed(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.vsspeed = index
        return ERROR_CODE[error] 
    
    def GetNumberPreAmpGains(self):
        noGains = c_int()
        error = self.dll.GetNumberPreAmpGains(byref(noGains))
        self.noGains = noGains.value
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetPreAmpGain(self):
        gain = c_float()

        self.preAmpGain = []

        for i in range(self.noGains):
            self.dll.GetPreAmpGain(i,byref(gain))
            self.preAmpGain.append(gain.value)

    def SetPreAmpGain(self, index):
        error = self.dll.SetPreAmpGain(index)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        self.preampgain = index
        return ERROR_CODE[error]

    def SetTriggerMode(self, mode):
        error = self.dll.SetTriggerMode(mode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

    def GetStatus(self):
        status = c_int()
        error = self.dll.GetStatus(byref(status))
        self.status = ERROR_CODE[status.value]
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
        
    def GetSeriesProgress(self):
        acc = c_long()
        series = c_long()
        error = self.dll.GetAcquisitionProgress(byref(acc),byref(series))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return series.value
        else:
            return None
             
    def GetAccumulationProgress(self):
        acc = c_long()
        series = c_long()
        error = self.dll.GetAcquisitionProgress(byref(acc),byref(series))
        if ERROR_CODE[error] == "DRV_SUCCESS":
            return acc.value
        else:
            return None
        
    def SetFrameTransferMode(self, frameTransfer):
        error = self.dll.SetFrameTransferMode(frameTransfer)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
        
    def SetShutterEx(self, typ, mode, closingtime, openingtime, extmode):
        error = self.dll.SetShutterEx(typ, mode, closingtime, openingtime, extmode)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]
        
    def SetSpool(self, active, method, path, framebuffersize):
        error = self.dll.SetSpool(active, method, c_char_p(path), framebuffersize)
        self.verbose(ERROR_CODE[error], sys._getframe().f_code.co_name)
        return ERROR_CODE[error]

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
