
# Import numpy and matplotlib 

import numpy as np  
import os
import logging
import matplotlib.pyplot as plt
from ctypes import *
import time
logger = logging.getLogger(__name__)
dll = CDLL(os.path.join("C:\Windows\System32", "imaq.dll"))

fig = plt.figure () 


#Define Functions: 


def Initialize (interfacename): 

    ID_pointer = c_ulong(0)
    # ID_pointer directs to interface ID
    error = dll.imgInterfaceOpen(interfacename, byref(ID_pointer))
    if error != 0:
        logger.warning("Error in imgInterfaceOpen: {}".format(error))
    logger.info("ID_Pointer={}".format(ID_pointer.value))

    Sess_ID = c_ulong(0)
    # generate session ID
    error = dll.imgSessionOpen(ID_pointer, byref(Sess_ID))
    if error != 0:
        logger.warning("Error in imgSessionOpen: {}".format(error))
    logger.info("Sess_ID={}".format(Sess_ID.value))
    
    height = c_uint(0)
    width = c_uint(0)
    top = c_uint(0)
    left=c_uint(0)
    error = dll.imgSessionGetROI(Sess_ID, byref(top), byref(left), byref(height), byref(width))
    bufferpointertype = c_uint16 * height.value * width.value
    bufferpointer = bufferpointertype()

    sizeNeeded = c_ulong(0)
    error = dll.imgSessionGetBufferSize(Sess_ID,byref(sizeNeeded))  # Get size of image 
    if error !=0:
        logger.warning("Error in imgSessionGetBufferSize: {}".format(error))
    logger.info("sizeNeeded={}".format(sizeNeeded.value))

    IMG_HOST_FRAME = c_int(0)
    return ID_pointer,Sess_ID,height,width,bufferpointer


def Video (bpnp,artist,bufferpointer):

    while True:
        dll.imgGrab(Sess_ID, byref(pointer(bufferpointer)), 0)    
        logger.info("grabbed frame "
                    "{} {} {}".format(bpnp.shape, bpnp[0, 0],
                                      np.ctypeslib.as_array(bufferpointer)[0, 0]
                                      )
                    )
        artist.autoscale()
        fig.canvas.draw()
        fig.canvas.flush_events()
        time.sleep(.2)
    error = dll.imgClose(Sess_ID, 1)


def WriteSerial(Sess_ID, mystring, timeout=1000):                                 # establish Serial communication
    stringtosend = c_char_p('{}\r'.format(mystring))  
    #print stringtosend.value
    sizeofstringtosend = c_ulong(len(stringtosend.value))
    #print "sizeofstringtosend={}".format(sizeofstringtosend)
    error = dll.imgSessionSerialWrite(Sess_ID, stringtosend, byref(sizeofstringtosend), timeout)  # Set Serial communication
    CheckError(error)
    bufsize, buffer = ReadSerial(Sess_ID, timeout) #check for response from camera
    return buffer  #return response from camera


def ReadSerial(Sess_ID, timeout=1000):                                 # establish Serial communication
    bufSize = c_int(100)
    buffer = c_char_p(' '*bufSize.value)
    error = dll.imgSessionSerialRead(Sess_ID, buffer, byref(bufSize), timeout)  # Set Serial communication
    CheckError(error)
    return bufSize.value, buffer.value
    

def StartVideo(Sess_ID):                                       # Start data aquistion
    WriteSerial(Sess_ID, 'AMD N')        # Free running mode
    WriteSerial(Sess_ID, 'SMD N')        # Scan Mode Normal (no binning)
    WriteSerial(Sess_ID, 'BGC F')        # Background Control Off
    exptime = WriteSerial(Sess_ID, 'AET 0.07')
    WriteSerial(Sess_ID, 'EMG 100.36')
    rotime = WriteSerial(Sess_ID, '?RAT') #ask for exposure time

    logger.info("Acquire Exposure time in seconds = {}".format(exptime))
    logger.info("Readout time in seconds = {}".format(rotime))

    logger.info(WriteSerial(Sess_ID, '?CAI T'))
    logger.info(WriteSerial(Sess_ID, '?CAI H'))
    logger.info(WriteSerial(Sess_ID, '?CAI V'))
    logger.info(WriteSerial(Sess_ID, '?CAI A'))
    logger.info(WriteSerial(Sess_ID, '?CAI I'))
    logger.info(WriteSerial(Sess_ID, '?CAI S'))
    logger.info(WriteSerial(Sess_ID, '?CAI B'))
    logger.info(WriteSerial(Sess_ID, '?CAI C'))
    logger.info(WriteSerial(Sess_ID, '?CAI N'))


def StartExperiment(Sess_ID):            # Start data aquistion
    WriteSerial(Sess_ID, 'AMD E')        # Free running mode
    WriteSerial(Sess_ID, 'EMD E')        # Free running mode
    WriteSerial(Sess_ID, 'SMD N')        # Scan Mode Normal (no binning)
    WriteSerial(Sess_ID, 'BGC F')        # Background Control Off
    WriteSerial(Sess_ID, 'AET 0.03052')
    WriteSerial(Sess_ID, '?RAT') #ask for exposure time
    exptimelen, exptime = ReadSerial(Sess_ID)
    logger.info("String length = {} Exposure time = {}".format(exptimelen,
                                                               exptime))


def StartAcquire(Sess_ID,bufferpointer,height,width):
    # Setup. The "one" tells it to start the aquistion immediately
    error = dll.imgGrabSetup(Sess_ID, 1)
    CheckError(error)

    fig.clf()
    ax = fig.add_subplot(111)
    bpnp = np.reshape(np.ctypeslib.as_array(bufferpointer),(height.value,width.value))
    artist = ax.imshow(bpnp)
    fig.show()
    logger.info("fig shown")
    return bpnp, artist


def CheckError(error):    # Check for error in serial communication
    if error != 0:
        logger.warning("Error in imgSessionSerialWrite: {}".format(error))
        logger.warning("{}".format(c_char_p(' '*257)))


interfacename = c_char_p('img0')   # Interface name 

logger.info("Interface Name: {}".format(interfacename.value))
# Initialize
ID_pointer, Sess_ID, height, width, bufferpointer = Initialize(interfacename)



logger.info("About to do GrabSetup")

StartVideo(Sess_ID)
# Start aquisition
bpnp, artist = StartAcquire(Sess_ID, bufferpointer, height, width)

Video(bpnp, artist, bufferpointer)   # View images as video



