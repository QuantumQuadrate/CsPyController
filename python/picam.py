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
import os, threading, time
import numpy
from atom.api import Int, Tuple, List, Str, Float, Bool, Member, observe
from instrument_property import IntProp, FloatProp
from cs_instruments import Instrument
from TCP import CsSock, CsClientSock
import subprocess
import socket, struct, threading, traceback

# imports for viewer
from analysis import AnalysisWithFigure
from colors import my_cmap
from enaml.application import deferred_call

# import random library for the function which generates sample images
import random

from PiParameterLookup import *

def pointer(x):
    """Returns a ctypes pointer"""
    ptr = ctypes.pointer(x)
    return ptr

class PICam(Instrument):

    AdcEMGain = Member()
    preAmpGain = Member()
    exposureTime = Member()
    triggerMode = Int()
    shotsPerMeasurement = Member()
    roilowh = Int(0)
    roihighh = Int(512)
    roilowv = Int(-512)
    roihighv = Int(0)
    roimaxh = Int(512)
    roimaxv = Int(-512)
    
    useDemo = True

    width = Int()  # the number of columns
    height = Int()  # the number of rows
    dim = Int()  # the total number of pixels
    serial = Str()  # the serial number of the camera
    #c_image_array = Member()  # a c_int array to store incoming image data
    available = Member() # data structure to store returned data from PiCam
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
    cameraHandle = Member()
    videoStarted = Bool()
    ChildProcess = Member()
    
    updatelock = Bool()
    
    ROI = Member()
    
    sock = Member()
    
    c_image_array = Member()
    data = Member()  # holds acquired images until they are written
    mode = Str('experiment')  # experiment vs. video
    analysis = Member()  # holds a link to the GUI display
    dll = Member()

    def __init__(self, name, experiment, description=''):
        super(PICam, self).__init__(name, experiment, description)
        self.AdcEMGain = IntProp('AdcEMGain', experiment, 'Picam EM gain', '0')
        #self.preAmpGain = IntProp('preAmpGain', experiment, 'Picam analog gain', '0')
        self.exposureTime = FloatProp('exposureTime', experiment, 'exposure time for edge trigger', '0')
        self.shotsPerMeasurement = IntProp('shotsPerMeasurement', experiment, 'number of expected shots', '0')
        self.properties += ['AdcEMGain', 'preAmpGain', 'exposureTime', 'triggerMode', 'shotsPerMeasurement']
        #self.ChildProcess = subprocess.Popen(['picamAdvanced.exe',''])

    def __del__(self):
        #print "Calling __del__ on Picam"
        if self.isInitialized:
            self.ShutDown()
        #self.ChildProcess.terminate()

    def initialize(self):
        """Starts the dll and finds the camera."""
        #Here we'll need to launch the C process, then check we can communicate with it.
        self.sock = CsClientSock("127.0.0.1",2153)
        #logger.warning("Sending Hello message to C++ program")
        self.sock.sendmsg('Hello')
        #logger.warning("Receiving Hello reply from C++ program")
        returnedmessage = self.sock.receive()
        #logger.warning('Received message: {}'.format(returnedmessage))
        
        self.InitializeCamera()
        #self.GetCameraSerialNumber()
        self.sock.sendmsg("COOL 1")   #Cooling fan on.
        returnedmessage = self.sock.receive()
        #logger.warning('Received message: {}'.format(returnedmessage))
        

        self.isInitialized = True

    def GetNumberNewImages(self): 
        self.sock.sendmsg('GNNI')
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Get Number New Images failed.\nMessage returned from C++: {}".format(returnedmessage[0:3]))
            raise PauseError
        ack, comm, value = returnedmessage.split()
        #logger.warning("Parameter {} value: {}\n".format(param,int(value)))
        return 0, int(value)
        
    def start_server(self):
        subprocess.Popen(['..\\cpp\\Picam\\projects\\vs2010\\bin\\x64\\Release\\Advanced.exe'])

    
    def start(self):
        #get images to clear out any old images
        #self.DumpImages()
        #declare that we are done now
        self.isDone = True

    def update(self):
        if self.enable:
            self.mode = 'experiment'
            if self.IsAcquisitionRunning():
                self.AbortAcquisition()
            self.GetDetector()
            self.setROIvalues()
            #self.SetPreAmpGain(self.preAmpGain.value)
            self.SetAdcEMGain(self.AdcEMGain.value)
            self.SetExposureTime(self.exposureTime.value)
            if self.triggerMode == 0:
                # set edge trigger
                '''
                typedef enum PicamTriggerDetermination
                {
                    PicamTriggerDetermination_PositivePolarity = 1,
                    PicamTriggerDetermination_NegativePolarity = 2,
                    PicamTriggerDetermination_RisingEdge       = 3,
                    PicamTriggerDetermination_FallingEdge      = 4
                } PicamTriggerDetermination; /* (5) */
                '''
                self.SetTriggerDetermination(3)
            else:
                # set level trigger
                self.SetTriggerDetermination(1)
            #self.SetImage(1, 1, 1, self.width, 1, self.height)  # full sensor, no binning
            
            self.setSingleROI(self.ROI[0], self.ROI[1], self.ROI[2], self.ROI[3], self.ROI[4], self.ROI[5])
            self.CreateAcquisitionBuffer()
            self.data = []
            #self.SetKineticCycleTime(0)  # no delay
            self.sock.sendmsg("CMTP")
            returnedmessage = self.sock.receive()
            if (returnedmessage[0:3]!='ACK'):
                logger.error("Failed to commit parameters. Returned message: {}".format(returnedmessage))
                raise PauseError
            #self.StartAcquisition()
            self.sock.sendmsg("KLCB")
            returnedmessage = self.sock.receive()
            if (returnedmessage[0:3]!='ACK'):
                logger.error("Failed to commit parameters. Returned message: {}".format(returnedmessage))
                raise PauseError

    def setup_video_thread(self, analysis):
        thread = threading.Thread(target=self.setup_video, args=(analysis,))
        #thread.daemon = True
        thread.start()
    

    def setROIvalues(self):
        if (self.roilowh < self.roihighh):
            self.ROI[0] = self.roilowh   #x
            self.ROI[1] = self.roihighh - self.roilowh   #width
        elif (self.roilowh > self.roihighh):
            self.ROI[0] = self.roihighh   #x
            self.ROI[1] = self.roilowh - self.roihighh   #width
        else:
            self.ROI[0] = self.roihighh
            self.ROI[1] = 1
        self.ROI[2] = 1   #x-binning
        
        if (self.roilowv < self.roihighv):
            self.ROI[3] = -self.roihighv   #x
            self.ROI[4] = self.roihighv - self.roilowv   #width
        elif (self.roilowv > self.roihighv):
            self.ROI[3] = -self.roilowv   #x
            self.ROI[4] = self.roilowv - self.roihighv   #width
        else:
            self.ROI[3] = self.roihighv
            self.ROI[4] = 1
        self.ROI[5] = 1   #y-binning
        
        
        self.width = self.ROI[1]
        self.height = self.ROI[4]
        self.dim = self.width*self.height
        #print "ROI values are: {} {} {} {} {} {}".format(*self.ROI)
        
    def setSendROIvalues(self):
        if self.updatelock == False:
            try:
                self.updatelock = True
                modeorig = ''
                if self.mode == 'video':
                    modeorig = 'video'
                    self.stop_video()
                time.sleep(1)
                if (self.roilowh < self.roihighh):
                    self.ROI[0] = self.roilowh   #x
                    self.ROI[1] = self.roihighh - self.roilowh   #width
                elif (self.roilowh > self.roihighh):
                    self.ROI[0] = self.roihighh   #x
                    self.ROI[1] = self.roilowh - self.roihighh   #width
                else:
                    self.ROI[0] = self.roihighh
                    self.ROI[1] = 1
                self.ROI[2] = 1   #x-binning
                
                if (self.roilowv < self.roihighv):
                    self.ROI[3] = -self.roihighv   #x
                    self.ROI[4] = self.roihighv - self.roilowv   #width
                elif (self.roilowv > self.roihighv):
                    self.ROI[3] = -self.roilowv   #x
                    self.ROI[4] = self.roilowv - self.roihighv   #width
                else:
                    self.ROI[3] = self.roihighv
                    self.ROI[4] = 1
                self.ROI[5] = 1   #y-binning
                self.width = self.ROI[1]
                self.height = self.ROI[4]
                self.dim = self.width*self.height
                self.setSingleROI(self.ROI[0], self.ROI[1], self.ROI[2], self.ROI[3], self.ROI[4], self.ROI[5])
                time.sleep(1)
                if modeorig == 'video':
                    self.setup_video_thread(self.analysis)
                #print "ROI values are: {} {} {} {} {} {}".format(*self.ROI)
            except:
                logger.error("Exception in setSendROIValues")
                raise PauseError
            finally:
                self.updatelock = False
                
        
    def setup_video(self, analysis):
        if self.experiment.status != 'idle':
            logger.warning('Cannot start video mode unless experiment is idle.')
            return
        self.mode = 'video'
        self.videoStarted = False
        self.analysis = analysis
        
        if not self.isInitialized:
            self.initialize()
        self.sock.clearbuffer()   #clear socket's buffer to kill off any old messages
        #if self.IsAcquisitionRunning():
        self.AbortAcquisition()
        
        self.GetDetector()
        self.setROIvalues()
        #self.SetPreAmpGain(self.preAmpGain.value)
        self.SetAdcEMGain(self.AdcEMGain.value)
        self.SetExposureTime(self.exposureTime.value)
        #self.SetTriggerMode(0)
        #self.SetImage(1, 1, 1, self.width, 1, self.height)  # full sensor, no binning
        self.setSingleROI(self.ROI[0], self.ROI[1], self.ROI[2], self.ROI[3], self.ROI[4], self.ROI[5])
        self.setPicamParameterLongInt(c_int(PicamParameter_ReadoutCount).value,1) #run continuously until Picam_StopAcquisition is called
        #self.SetKineticCycleTime(0)  # no delay

        #print self.width, self.height, self.dim
        self.data = self.CreateAcquisitionBuffer()
        analysis.setup_video(self.data)
        
        self.sock.sendmsg("CMTP")   #Commit Parameters
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3]!='ACK'):
            logger.error("Failed to commit parameters. Returned message: {}".format(returnedmessage))
            raise PauseError
        self.StartAcquisition()
        #self.StartVideo()

        # run the video loop in a new thread
        self.start_video_thread()
        #thread = threading.Thread(target=self.start_video_thread)
        #thread.daemon = True
        #thread.start()

    def start_video_thread(self):
        while self.mode == 'video':
            self.GetImages()
                # if there is new data, then redraw image
            self.analysis.redraw_video()
            time.sleep(.01)
            if (self.videoStarted != True):
                self.StartVideo()
                self.videoStarted = True

    def stop_video(self):
        # stop the video thread from looping
        self.mode = 'idle'
        time.sleep(1)
        self.AbortAcquisition()

    """
    check_error takes as arguments an error code returned by the Picam DLL and a string.
    The error code is translated into a string, and if it doesn't match the "None" code (which indicates no error), it logs the error and includes the string 'funcname', which is used to indicate where in the Python code the error occurred.
    """     
    def check_error(self,errcode,funcname):
        if errcode != "PicamError_None":  #if there's an error, log it.
            logger.error('Error in {}:\n{}'.format(funcname,errcode))
            raise PauseError
        
    def acquire_data(self):
        """Overwritten from Instrument, this function is called by the experiment after
        each measurement run to make sure all pictures have been acquired."""
        if self.enable:
            self.data = self.GetImages()

    def writeResults(self, hdf5):
        """Overwritten from Instrument.  This function is called by the experiment after
        data acquisition to write the obtained images to hdf5 file."""
        if self.enable:
            try:
                hdf5['Picam'] = self.data
            except Exception as e:
                logger.error('in Picam.writeResults:\n{}'.format(e))
                raise PauseError

    def InitializeCamera(self):
        #if useDemo is True, connect a demo camera
        if (self.useDemo):
            logger.debug('Connecting Demo Camera... ')
            self.sock.sendmsg('CDMC 604 Demo_Cam_1')
            returnedmessage = self.sock.receive()
            logger.debug('Reply from C++ code: {}'.format(returnedmessage))
        #send Open Camera command
        self.sock.sendmsg('OFCM')
        returnedmessage = self.sock.receive()
        logger.debug('Reply from C++ code: {}'.format(returnedmessage))

    def GetImages(self):
        #first, last = self.GetNumberNewImages()
        if (self.mode == 'video' or self.mode == 'idle'):
            acquiredimages = 1
            self.sock.sendmsg("ACQI")
            returnedmessage = self.sock.receive()
            if (returnedmessage[0:3]!='ACK'):
                logger.error("Failed to get image. Returned message: {}".format(returnedmessage))
                return
            if (returnedmessage[4:8]!='ACQI'):
                logger.error("Returned message to GetImages from C++ not matching Acquire Image request. Returned message: {}".format(returnedmessage))
                return
        else:
            acquiredimages = self.shotsPerMeasurement.value
            logger.debug("Requesting {} images".format(acquiredimages))
            self.sock.sendmsg("AQMI {}".format(acquiredimages))
            returnedmessage = self.sock.receive()
            if (returnedmessage[0:3]!='ACK'):
                logger.error("Failed to get images. Returned message: {}".format(returnedmessage))
                raise PauseError
            if (returnedmessage[4:8]!='AQMI'):
                logger.error("Returned message to GetImages from C++ not matching Acquire Multiple Image request. Returned message: {}".format(returnedmessage))
                raise PauseError

        imagedatastr = returnedmessage[9:]
        imagedatalen = len(imagedatastr)/2  #16-bit data...
        if (imagedatalen != self.dim*acquiredimages):
            logger.warning("GetImages(): imagedatalen != self.dim. Possibly missing data...")
        try:
            imagedata=struct.unpack(""+str(imagedatalen)+"H", imagedatastr)
        except Exception as e:
            logger.warning('incorrectly formatted message: does not have 2 byte unsigned short for length. '+str(e))
            logger.warning('Message length: {} bytes'.format(len(imagedatastr)))
            raise PauseError
        if (self.width*(self.height)*acquiredimages != imagedatalen):
            logger.error("Image data dimensions do not match expected dims: {}x{} {} bytes. Received: {} bytes".format(self.width,self.height,self.dim,imagedatalen))
            #logger.error("Returned Message from C++: {}".format(returnedmessage))
            raise PauseError
        
        if (self.mode == 'video'):
            starttime = time.clock()
            i=0
            while (i<self.width*self.height):
                self.c_image_array[i] = imagedata[i]
                #j=0
                #while (j<self.height):
                    #self.c_image_array[i+j*(self.width)] = imagedata[i+j*(self.width)]
                    #j=j+1
                i=i+1
            #ctypes.memmove(self.c_image_array, (ctypes.c_int * len(imagedata))(*imagedata), self.width*self.height*ctypes.sizeof(ctypes.c_int))
            endtime = time.clock()
            logger.debug("Time elapsed while copying into c_image_array: {} seconds".format(endtime-starttime))
            return imagedata
        if (self.mode == 'idle'):
            return self.data
        
        #Allocate space for temp c_image_array...
        size = self.dim * acquiredimages
        c_image_array_type = c_int * size
        c_image_array = c_image_array_type()
        i=0
        while (i<self.width*self.height*acquiredimages):
            c_image_array[i] = imagedata[i]
            #j=0
            #while (j<self.height*acquiredimages):
            #    c_image_array[i+j*(self.width)] = imagedata[i+j*(self.width)]
            #    j=j+1
            i=i+1
        #logger.warning("Reshaping numpy array")
        framedata = numpy.ctypeslib.as_array(c_image_array)
        framedata = numpy.reshape(framedata, (acquiredimages, self.height, self.width))
        if (len(self.data)>0):
            #logger.warning("self.data: {}".format(self.data))
            data = numpy.append(self.data,framedata,axis=0)
        else:
            data = framedata
        return data
        
        
    '''
      This function randomly generates an image, which is stored in the C array cArray.
    '''    
    def GenerateSampleImage(self,readoutcount,readoutstride,cArray):
        numberofbytes = readoutstride*readoutcount/2
        i = 0
        while (i<numberofbytes):
            cArray[i] = random.randint(0,65535)
            i=i+1
    

    def DumpImages(self):
        while True:
            available = PicamAvailableData()
            Picam_Acquire.argtypes = PicamHandle, pi64s, piint, ctypes.POINTER(PicamAvailableData), ctypes.POINTER(PicamAcquisitionErrorsMask)
            Picam_Acquire.restype = piint
            error = PICam_Acquire(self.cameraHandle, pi64s(1), piint(1), byref(available), byref(errors))
            if available.readout_count == 0:
                break

    def GetDetector(self):
        self.width = self.getPicamParameterInt(ctypes.c_int(PicamParameter_SensorActiveWidth).value)
        self.height = self.getPicamParameterInt(ctypes.c_int(PicamParameter_SensorActiveHeight).value)
        self.roimaxv = -self.height
        self.roimaxh = self.width
        self.width = self.width - 1
        self.height = self.height - 1   # -2 because height gets reported as 1004 instead of 1002 for Luca
        self.ROI = [0, self.width, 1, 0, self.height, 1 ];   #setting default ROI to be full field.
        self.dim = self.width * self.height
        #print 'PICam: width {}, height {}'.format(self.width, self.height)
        #print 'PICam dim: {}'.format(self.dim)
        return self.width, self.height

    def AbortAcquisition(self):
        self.sock.sendmsg("HLAQ")
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Halt Acquisition {} failed.\nMessage returned from C++: {}".format(param, returnedmessage))
            raise PauseError

    def ShutDown(self):
        self.sock.sendmsg("CLOS")
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Close Camera {} failed.\nMessage returned from C++: {}".format(param, returnedmessage))
            #raise PauseError
        

    def GetCameraSerialNumber(self):
        seriallist = PicamCameraID()
        arrlen = piint()
        self.check_error(Picam_GetAvailableCameraIDs(byref(seriallist),byref(arrlen)),"Picam_GetAvailableCameraIDs")
        if (arrlen.value == 0):
            logger.error('No cameras found in Picam_GetAvailableCameraIDs:\n')
            raise PauseError
        if (arrlen.value > 1):   #This API can handle multiple cameras, but this version of the Python code assumes one camera...
            logger.error('Multiple cameras found in Picam_GetAvailableCameraIDs:\n')
            raise PauseError    
        self.serial = seriallist.serial_number
        return self.serial

    def StartVideo(self):
        self.sock.sendmsg("STVD")   #Start Video
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3]!='ACK'):
            logger.error("Failed to commit parameters. Returned message: {}".format(returnedmessage))
            raise PauseError  

    def StartAcquisition(self):
        self.sock.sendmsg("STAQ")
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Start Acquisition {} failed.\nMessage returned from C++: {}".format(param, returnedmessage))
            raise PauseError

    def CreateAcquisitionBuffer(self):
        """This function creates an image buffer to be used for video display.
        The buffer will be updated by the GetMostRecentImage method, to give the fastest
        possible update.  A numpy array that uses the same memory space as the c array is returned.
        That way plotting functions like matplotlib can be used and the plot data can be
        automatically updated whenever new data is available.  All that needs to be done is for the
        plot to be redrawn whenever a new image is captured."""

        c_image_array_type = c_int * self.dim
        self.c_image_array = c_image_array_type()

        data = numpy.ctypeslib.as_array(self.c_image_array)
        data = numpy.reshape(data, (self.height, self.width))
        return data

#    def GetMostRecentImage(self):
#        """This function gets the most recent image, for video display.
#        It must be preceded by a call to CreateAcquisitionBuffer() and StartAcquisition().
#        The image data is put into self.c_image_array, which must already be allocated (by Create AcquisitionBuffer)."""
#
#        error = self.dll.GetMostRecentImage(byref(self.c_image_array), self.dim)
#        if ERROR_CODE[error] != 'DRV_SUCCESS':
#            logger.error('Error:\n{}'.format(ERROR_CODE[error]))
#            #raise PauseError
#            return False
#        return True

    def SetExposureTime(self, time):
        self.setPicamParameterFP(ctypes.c_int(PicamParameter_ExposureTime).value,time)

    def setPicamParameterInt(self, param, value):
        self.sock.sendmsg("SPIN {} {}".format(param,value))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Set Integer Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage))
            raise PauseError
            
    def setPicamParameterLongInt(self, param, value):
        self.sock.sendmsg("SPLI {} {}".format(param,value))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Set Long Integer Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage))
            raise PauseError
            
            
    def setPicamParameterFP(self, param, value):
        self.sock.sendmsg("SPFP {} {}".format(param,value))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Set Floating Point Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage))
            raise PauseError
            
            
    def getPicamParameterInt(self, param):
        self.sock.sendmsg("GPIN {}".format(param))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Get Integer Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage[0:3]))
            raise PauseError
        ack, comm, value = returnedmessage.split()
        #logger.warning("Parameter {} value: {}\n".format(param,int(value)))
        return int(value)
            
    def getPicamParameterLongInt(self, param):
        self.sock.sendmsg("GPLI {}".format(param))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Get Long Integer Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage))
            raise PauseError
        ack, par, value = returnedmessage.split()
        return long(value)
            
            
    def getPicamParameterFP(self, param):
        self.sock.sendmsg("GPFP {}".format(param))
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != "ACK"):
            logger.error("Get Floating Point Parameter {} failed.\nMessage returned from C++: {}".format(PicamParamDict[str(param%65536)], returnedmessage))
            raise PauseError
        ack, par, value = returnedmessage.split()
        return float(value)


    def GetTemperature(self):
        temperature = self.getPicamParameterFP(ctypes.c_int(PicamParameter_SensorTemperatureReading).value)
        self.temperature = temperature
        return self.temperature

    def SetTemperature(self, temperature):
        self.setPicamParameterFP(ctypes.c_int(PicamParameter_SensorTemperatureSetPoint).value,temperature)
        self.set_T = temperature

    def GetAnalogGain(self):
        self.gain = self.getPicamParameterInt(ctypes.c_int(PicamParameter_AdcAnalogGain).value)
        
    def GetAdcEMGain(self):
        self.gain = self.getPicamParameterInt(ctypes.c_int(PicamParameter_AdcEMGain).value)

    def SetAdcEMGain(self, gain):
        self.setPicamParameterInt(ctypes.c_int(PicamParameter_AdcEMGain).value,gain)
        

    def SetTriggerDetermination(self,determ):
        self.setPicamParameterInt(ctypes.c_int(PicamParameter_TriggerDetermination).value,determ)
        
        
    def SetTriggerResponse(self,resp):
        self.setPicamParameterInt(ctypes.c_int(PicamParameter_TriggerResonse).value,resp)
        
        
    def IsAcquisitionRunning(self):
        self.sock.sendmsg("ISAR")
        returnedmessage = self.sock.receive()
        if (returnedmessage == "ACK ISAR 1"):
            status = True
            logger.warning("Acquisition is running.")
        elif (returnedmessage == "ACK ISAR 0"):
            status = False
            logger.warning("Acquisition is NOT running.")
        else:
            status = False
            logger.error("Received message from C++ code after sending IsAcquisitionRunning: {}".format(returnedmessage))
            raise PauseError
        return status

    """
    setROIs(rois) is a function which accepts as an argument a
    set of regions of interest in a PicamRois structure.
    The structure has two elements:
        roi_array, which is an array (in C, a pointer to) of PicamRoi structures.
        roi_count, type piint, which is the number of elements in roi_array.
    This sets the Rois parameter on the camera, enabling regions of interest to be set.
    """     
#    def setROIs(self,rois):
#        self.check_error(Picam_SetParameterRoisValue(self.cameraHandle,ctypes.c_int(PicamParameter_Rois),rois),"setROIs")

        
        
    """
    setSingleROI(roi) is a function which accepts as an argument a single region of interest (PicamRoi) structure.
    This structure has six elements, all of type piint:
        x: left-most column, starting from zero
        width: number of columns
        x_binning: number of columns to group into sums
        y: top-most row, starting from zero
        height: number of rows
        y_binning: number of rows to group into sums.
    This puts the single ROI into a PicamRois structure and passes
    it to setROIs().
    """
    def setSingleROI(self,x,width,x_binning,y,height,y_binning):
        self.sock.sendmsg("ROI  {} {} {} {} {} {}".format(x,width,x_binning,y,height,y_binning))
        #print "Sending ROI: {} {} {} {} {} {} ".format(x,width,x_binning,y,height,y_binning)
        returnedmessage = self.sock.receive()
        if (returnedmessage[0:3] != 'ACK'):
            logger.error("Error setting single ROI: message from C++ program: {}".format(returnedmessage))
            logger.error("ROI Values: {}, {}, {}, {}, {}, {}".format(x,width,x_binning,y,height,y_binning))
        
        
        
        

class PICamViewer(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    shot = Int(0)
    update_lock = Bool(False)
    artist = Member()

    def __init__(self, name, experiment, description=''):
        super(PICamViewer, self).__init__(name, experiment, description) 
        self.properties += ['shot']

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        if 'data/Picam' in measurementResults:
            #for each image
            self.data = measurementResults['data/Picam']
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot')
    def reload(self, change):
        self.updateFigure()
    
    def updateFigure(self):
        if not self.update_lock and (self.experiment.PICam.mode != 'video'):
            try:
                self.update_lock = True
                fig = self.backFigure
                fig.clf()

                if (self.data is not None) and (self.shot < len(self.data)):
                    ax = fig.add_subplot(111)
                    ax.matshow(self.data[self.shot], cmap=my_cmap)
                    ax.set_title('most recent shot '+str(self.shot))
                #else:
                #    logger.warning("self.data is None, or self.shot > len(self.data)\nself.data: {}\nlen(self.data): {}".format(self.data,len(self.data)))
                super(PICamViewer, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in PicamViewer.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False
      
    def setup_video(self, data):
        """Use this method to connect the analysis figure to an array that will be rapidly updated
        in video mode."""
        self.data = data
        fig = self.backFigure
        fig.clf()
        ax = fig.add_subplot(111)
        self.artist = ax.imshow(data)
        super(PICamViewer, self).updateFigure()

    def redraw_video(self):
        """First update self.data using Andor methods, then redraw screen using this."""
        self.artist.autoscale()
        deferred_call(self.figure.canvas.draw)
        
        
