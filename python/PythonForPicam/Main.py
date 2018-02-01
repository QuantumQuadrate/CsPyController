"""
PythonForPicam is a Python ctypes interface to the Princeton Instruments PICAM Library
    Copyright (C) 2013  Joe Lowney.  The copyright holder can be reached at joelowney@gmail.com

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or any 
    later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    
"""

"""Test for talking to Picam"""
import ctypes as ctypes

from PiParameterLookup import *

from PythonForPicam import *

import numpy as np
import matplotlib.pyplot as plt

import sys

############################
##### Custom Functions #####
############################
    
def pointer(x):
    """Returns a ctypes pointer"""
    ptr = ctypes.pointer(x)
    return ptr


def load(x):
    """Loads DLL library where argument is location of library"""
    x = ctypes.cdll.LoadLibrary(x)
    return x

#########################
##### Main Routine  #####
#########################

if __name__ == '__main__':

    """ Load the picam.dll """
    #picamDll = 'C:/Users/becgroup/Documents/Python/DriverTest/Princeton Instruments/Picam/Runtime/Picam.dll'
    #picamDll = 'DLLs/Picam.dll'
    picamDll = 'C:/Program Files/Common Files/Princeton Instruments/Picam/Runtime/Picam.dll'

    picam = load(picamDll)
    
    print 'Initialize Camera.',Picam_InitializeLibrary()
    print '\n'

    """ Print version of PICAM """
    major = piint()
    minor = piint()
    distribution = piint()
    release = piint()
    print 'Check Software Version. ',Picam_GetVersion(pointer(major),pointer(minor),pointer(distribution),pointer(release))
    print 'Picam Version ',major.value,'.',minor.value,'.',distribution.value,' Released: ',release.value
    print '\n'

    ## Test Routine to connect a demo camera
    ## p23
    print 'Preparing to connect Demo Camera'   
    model = ctypes.c_int(10)
    serial_number = ctypes.c_char_p('Demo Cam 1')
    PicamID = PicamCameraID()  
    """
    PICAM_API Picam_ConnectDemoCamera(
    PicamModel     model,
    const pichar*  serial_number,
    PicamCameraID* id );
    """
    print 'Demo camera connetcted with return value = ',Picam_ConnectDemoCamera(model, serial_number, pointer(PicamID))
    print '\n'
    
    print 'Camera model is ',PicamID.model
    print 'Camera computer interface is ',PicamID.computer_interface
    print 'Camera sensor_name is ', PicamID.sensor_name
    print 'Camera serial number is', PicamID.serial_number
    print '\n'

    ## Test routine to open first camera
    ## p20
    """
    PICAM_API Picam_OpenFirstCamera( PicamHandle* camera );
    """
    camera = PicamHandle()
    print 'Opening First Camera', Picam_OpenFirstCamera(ctypes.addressof(camera))

    model = ctypes.c_int(10)
    serial_number = ctypes.c_char_p('Demo Cam 1')
    PicamID = PicamCameraID()  

    print 'Retrieving camera ID',Picam_GetCameraID(camera,  pointer(PicamID))
    print 'Camera model is ',PicamID.model
    print 'Camera computer interface is ',PicamID.computer_interface
    print 'Camera sensor_name is ', PicamID.sensor_name
    print 'Camera serial number is', PicamID.serial_number
    print '\n'

    ## Test routine to acquire image
    ## p73
    """
    PICAM_API Picam_Acquire(
    PicamHandle                 camera,
    pi64s                       readout_count,
    piint                       readout_time_out,
    PicamAvailableData*         available,
    PicamAcquisitionErrorsMask* errors );
    """
    readoutstride = piint(0)
    for i in [8,5]:
        print i+1
        print "Getting readout stride. ",Picam_GetParameterIntegerValue( camera, ctypes.c_int(PicamParameter_ReadoutStride), ctypes.byref(readoutstride) );
        print "The readoutstride is %d" % readoutstride.value
        """
        Prototype
        PICAM_API Picam_Acquire(
        PicamHandle                 camera,
        pi64s                       readout_count,
        piint                       readout_time_out,
        PicamAvailableData*         available,
        PicamAcquisitionErrorsMask* errors );
        """
    
        """
        typedef struct PicamAvailableData
        {
            void* initial_readout;
            pi64s readout_count;
        } PicamAvailableData;
        """
        Picam_SetParameterIntegerValue( camera, PicamParameter_TriggerResponse, PicamTriggerResponse_NoResponse)
        Picam_SetParameterIntegerValue( camera, PicamParameter_TriggerDetermination, PicamTriggerDetermination_PositivePolarity )
        Picam_SetParameterIntegerValue( camera, PicamParameter_OutputSignal, i+1 )
        exposure = piflt(10.)
        picam.Picam_SetParameterFloatingPointValue.argtypes=[PicamHandle, piint, piflt]
        status = Picam_SetParameterFloatingPointValue(camera, PicamParameter_ExposureTime, exposure)
        print " %s = Picam_SetParameterFloatingPointValue(camera, %d, "% (status,PicamParameter_ExposureTime,), exposure,")"
        failCount = piint()
        paramsFailed = piint()
        status = Picam_CommitParameters(camera, pointer(paramsFailed), ctypes.byref(failCount))
        print "commit returned ", status, "failCount is ",failCount
        readout_count = pi64s(4)
        readout_time_out = piint(100000)
        available = PicamAvailableData(0, 0)
    
        """ Print Debug Information on initial readout """
        print '\n'
        print "available.initial_readout: ",available.initial_readout
        print "Initial readout type is", type(available.initial_readout)
        errors = PicamAcquisitionErrorsMask()
    
        """
        Prototype
        PICAM_API Picam_Acquire(
        PicamHandle                 camera,
        pi64s                       readout_count,
        piint                       readout_time_out,
        PicamAvailableData*         available,
        PicamAcquisitionErrorsMask* errors );
        """
    #    Picam_Acquire.argtypes = PicamHandle, pi64s, piint, ctypes.POINTER(PicamAvailableData), ctypes.POINTER(PicamAcquisitionErrorsMask)
        Picam_Acquire.argtypes = [] 
        Picam_Acquire.restype = piint
        
        print '\nAcquiring... ',Picam_Acquire(camera, readout_count, readout_time_out, ctypes.byref(available),
                                              ctypes.byref(errors))
        print '\n'
    
        print "available.initial_readout: ",available.initial_readout
        print "Initial readout type is", type(available.initial_readout)
        print '\n'
        
    
        """ Test Routine to Access Data """
        
        """ Create an array type to hold 1024x1024 16bit integers """
        sz = readoutstride.value/2
        DataArrayType = pi16u*sz
    
        """ Create pointer type for the above array type """
        DataArrayPointerType = ctypes.POINTER(pi16u*sz)
    
        """ Create an instance of the pointer type, and point it to initial readout contents (memory address?) """
        DataPointer = ctypes.cast(available.initial_readout,DataArrayPointerType)
    
    
        """ Create a separate array with readout contents """
        data = DataPointer.contents
        ans = np.empty(sz,np.short)
        cnt = 0
        ans[:] = data
        ans = ans.reshape((512,512))
        plt.figure()
        plt.imshow(ans)
        plt.show()
    """ Write contents of Data to binary file"""

    print 'readoutstride is ', readoutstride.value

    # try to do rois
    rois = PicamRois(4)
    rois.roi_array[0].x = 0
    rois.roi_array[0].width = 512
    rois.roi_array[0].x_binning = 1
    rois.roi_array[0].y = 76
    rois.roi_array[0].height = 60
    rois.roi_array[0].y_binning = 60

    rois.roi_array[1].x = 0
    rois.roi_array[1].width = 512
    rois.roi_array[1].x_binning = 1
    rois.roi_array[1].y = 185
    rois.roi_array[1].height = 60
    rois.roi_array[1].y_binning = 60

    rois.roi_array[2].x = 0
    rois.roi_array[2].width = 512
    rois.roi_array[2].x_binning = 1
    rois.roi_array[2].y = 294
    rois.roi_array[2].height = 60
    rois.roi_array[2].y_binning = 60

    rois.roi_array[3].x = 0
    rois.roi_array[3].width = 512
    rois.roi_array[3].x_binning = 1
    rois.roi_array[3].y = 403
    rois.roi_array[3].height = 60
    rois.roi_array[3].y_binning = 60

    Picam_SetParameterRoisValue(camera, PicamParameter_Rois, pointer(rois))

    failCount = piint()
    paramsFailed = piint()
    Picam_CommitParameters(camera, pointer(paramsFailed), ctypes.byref(failCount))
    Picam_DestroyParameters(pointer(paramsFailed))

    readoutstride = piint(0);
    print "Getting readout stride. ",Picam_GetParameterIntegerValue( camera, ctypes.c_int(PicamParameter_ReadoutStride), ctypes.byref(readoutstride) );
    print "The readoutstride is %d" % readoutstride.value
    readout_count = pi64s(100)
    print '\nAcquiring... ',Picam_Acquire(camera, readout_count, readout_time_out, ctypes.byref(available),
                                          ctypes.byref(errors))
    print "available.initial_readout: ",available.initial_readout
    print "Initial readout type is", type(available.initial_readout)
    print '\n'
    

    """ Test Routine to Access Data """
    
    """ Create an array type to hold 1024x1024 16bit integers """
    sz = readout_count.value*readoutstride.value/2
    print "sz is ", sz
    DataArrayType = pi16u*sz

    """ Create pointer type for the above array type """
    DataArrayPointerType = ctypes.POINTER(pi16u*sz)

    """ Create an instance of the pointer type, and point it to initial readout contents (memory address?) """
    DataPointer = ctypes.cast(available.initial_readout,DataArrayPointerType)


    """ Create a separate array with readout contents """
    data = DataPointer.contents
    print "make the nparray"
    ans = np.empty(sz,np.short)
    ans[:] = data
    ans = ans.reshape((readout_count.value, readoutstride.value/2/512, 512))
    print ans.flags
    print ans.shape
    plt.figure()
    plt.plot(ans)
    plt.show()
    """ Write contents of Data to binary file"""

    print 'readoutstride is ', readoutstride.value
    print ans


    """ Close out Library Resources """
    print 'Uninitializing',Picam_UninitializeLibrary()
