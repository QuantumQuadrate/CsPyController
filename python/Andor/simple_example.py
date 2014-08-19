from andor import *
import time
import sys
import signal
import time
import matplotlib.pyplot as plt
import matplotlib.animation

#####################
# Initial settings  #
#####################

Tset = -20
EMCCDGain = 0
PreAmpGain = 0
mode = 'Run Till Abort'

def signal_handler(signal, frame):
    print 'Shutting down the camera...'
    cam.ShutDown()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Initialising the Camera
cam = Andor()
cam.GetCameraSerialNumber()
print 'serial #:',cam.serial

cam.SetReadMode(4)
print "width: {}, height: {}".format(cam.width, cam.height)
cam.width=1004
cam.height=1002
cam.SetImage(1,1,1,cam.width,1,cam.height)


cam.SetAcquisitionMode(5) # 1 = single, 5 = run till abort
cam.SetExposureTime(0.00001)
cam.SetKineticCycleTime(0) # for run till abort mode

cam.SetTriggerMode(0)

#cam.SetShutter(1,1,0,0)
cam.SetPreAmpGain(PreAmpGain)
cam.SetEMCCDGain(EMCCDGain)
cam.SetExposureTime(0.1)
cam.SetCoolerMode(1)

cam.SetTemperature(Tset)
cam.CoolerON()


cam.GetTemperature()
#while cam.GetTemperature() is not 'DRV_TEMP_STABILIZED':
print "Temperature is: %g [Set T: %g]" % (cam.temperature, Tset)
#    time.sleep(1)

if mode == 'Run Till Abort':
    cam.GetStatus()
    print "status:", cam.status
    if cam.status is not 'DRV_IDLE':
        print "Can't start acquisition if status is not idle"
        exit()
    else:
        print "Status is idle, ready for acquisition"

    errorValue = cam.StartAcquisition()
    print "Acquisition Start: ", errorValue
    if errorValue != 'DRV_SUCCESS':
        print "Start acquisition error"
        cam.AbortAcquisition()
        exit()
    
#plt.ion()
fig, ax = plt.subplots()

#data = numpy.zeros(cam.width*cam.height, dtype='int32')
#display_data = numpy.reshape(data, (cam.width, cam.height))
#cimage = numpy.ctypeslib.as_ctypes(data)
data = cam.CreateAcquisitionBuffer()
#imageArray = numpy.ctypeslib.as_array(cimage)
#imageArray = numpy.reshape(imageArray,(cam.width,cam.height))

artist = ax.imshow(data)
plt.show(block=False)

i = 0
t0 = time.time()

while True:

    # #cam.GetTemperature()
    # #print "Temperature is: %g [Set T: %g]" % (cam.temperature, Tset)

    # if mode == 'Single':
        # cam.GetStatus()
        # print "status:", cam.status
        # if cam.status is not 'DRV_IDLE':
            # print "Can't start acquisition if status is not idle"
            # exit()
        # else:
            # print "Status is idle, ready for acquisition"

        # errorValue = cam.StartAcquisition()
        # print "Acquisition Start: ", errorValue
        # if errorValue != 'DRV_SUCCESS':
            # print "Start acquisition error"
            # cam.AbortAcquisition()
            # break

        # cam.WaitForAcquisition()
        # #data = cam.GetAcquiredData()
    
    cam.GetMostRecentImage()

    #ax.cla()
    #ax.imshow(data)
    
    #artist.set_data(data)
    artist.autoscale()
    #artist.changed()
    #plt.show(block=False)
    
    fig.canvas.draw()
    
    i+=1
    print 'FPS: ',i/(time.time()-t0)

#ani = matplotlib.animation.FuncAnimation(fig, animate, repeat=True, interval=1)
    
#plt.show()

#cam.SaveAsBmpNormalised("%03g.bmp" %i)
#cam.SaveAsBmp("%03g.bmp" %i)
#cam.SaveAsTxt("%03g.txt" %i)

cam.shutDown()
