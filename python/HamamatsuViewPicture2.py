
# Import numpy and matplotlib 

import numpy as np  
import os,sys

import matplotlib.pyplot as plt
from ctypes import *
import time

dll = CDLL(os.path.join("C:\Windows\System32", "imaq.dll"))

fig = plt.figure () 


#Define Functions: 


def Initialize (interfacename): 

    ID_pointer = c_ulong(0)
    error = dll.imgInterfaceOpen(interfacename, byref(ID_pointer))  # ID_pointer directs to interface ID  
    if error !=0:
        print "Error in imgInterfaceOpen: {}".format(error)
    print "ID_Pointer={}".format(ID_pointer.value)

    Sess_ID = c_ulong(0)
    error = dll.imgSessionOpen(ID_pointer, byref(Sess_ID))   # generate session ID 
    if error !=0:
        print "Error in imgSessionOpen: {}".format(error)
    print "Sess_ID={}".format(Sess_ID.value)
    
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
        print "Error in imgSessionGetBufferSize: {}".format(error) 
    print "sizeNeeded={}".format(sizeNeeded.value)

    IMG_HOST_FRAME = c_int(0)
    return ID_pointer,Sess_ID,height,width,bufferpointer


def Video (bpnp,artist,bufferpointer):

    while(True):                                       
        dll.imgGrab(Sess_ID, byref(pointer(bufferpointer)), 0)    
        print "grabbed frame"
        print bpnp.shape
        print bpnp[0,0]
        print np.ctypeslib.as_array(bufferpointer)[0,0]
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

    print "Acquire Exposure time in seconds = {}".format(exptime)
    print "Readout time in seconds = {}".format(rotime)

    print WriteSerial(Sess_ID, '?CAI T')
    print WriteSerial(Sess_ID, '?CAI H')
    print WriteSerial(Sess_ID, '?CAI V')
    print WriteSerial(Sess_ID, '?CAI A')
    print WriteSerial(Sess_ID, '?CAI I')
    print WriteSerial(Sess_ID, '?CAI S')
    print WriteSerial(Sess_ID, '?CAI B')
    print WriteSerial(Sess_ID, '?CAI C')
    print WriteSerial(Sess_ID, '?CAI N')


def StartExperiment(Sess_ID):                                       # Start data aquistion
    WriteSerial(Sess_ID, 'AMD E')        # Free running mode
    WriteSerial(Sess_ID, 'EMD E')        # Free running mode
    WriteSerial(Sess_ID, 'SMD N')        # Scan Mode Normal (no binning)
    WriteSerial(Sess_ID, 'BGC F')        # Background Control Off
    WriteSerial(Sess_ID, 'AET 0.03052')
    WriteSerial(Sess_ID, '?RAT') #ask for exposure time
    exptimelen, exptime = ReadSerial(Sess_ID)
    print "String length = {} Exposure time = {}".format(exptimelen,exptime)


def StartAcquire(Sess_ID,bufferpointer,height,width):
    error = dll.imgGrabSetup(Sess_ID, 1)     # Setup. The "one" tells it to start the aquistion immediately 
    CheckError(error)

    fig.clf()
    ax = fig.add_subplot(111)
    bpnp = np.reshape(np.ctypeslib.as_array(bufferpointer),(height.value,width.value))
    artist = ax.imshow(bpnp)
    fig.show()
    print "fig shown"
    return bpnp,artist

def CheckError (error):                             # Check for error in serial communication
    if error !=0:
        print "Error in imgSessionSerialWrite: {}".format(error) 
        errorcode = c_char_p(' '*257)
        errorerror = dll.imgShowError(error, errorcode)
        print "{}".format(errorcode)





interfacename = c_char_p('img0')   # Interface name 

print "Interface Name: {}".format(interfacename.value)

ID_pointer,Sess_ID,height,width,bufferpointer = Initialize (interfacename)                # Initialize



print "About to do GrabSetup"

StartVideo(Sess_ID)
bpnp, artist = StartAcquire (Sess_ID,bufferpointer,height,width)   # Start aquisition

Video (bpnp,artist,bufferpointer)   # View images as video



