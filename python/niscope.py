"""NIScope.py
   Part of the AQuA Cesium Controller software package

   author=Martin Lichtman
   created=2014-07-28
   modified>=2014-07-30

   This code communicates with the NIScope Luca camera.  It can both get and set
   the settings of the camera, and read images.  Single shot and video modes are
   supported.

   The dll interface in this code is based on:
   pyNIScope - A Python wrapper for NIScope's scientific cameras
   Copyright (C) 2009  Hamid Ohadi

   NIScope class which is meant to provide the Python version of the same
   functions that are defined in the NIScope's SDK. Since Python does not
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

#https://code.google.com/archive/p/pyniscope/
try:
    from niScopeTypes import *
    import niScope
    niScopeImported = True
except:
    logger.warning('''pyniscope not installed. NI-SCOPE will not work. Run the following commands to install it:
    
    cd pyniscope-maser
    python setup.py build
    python setup.py install
    
    ''')
    niScopeImported = False

# imports for viewer
from analysis import AnalysisWithFigure, Analysis
from colors import my_cmap
from enaml.application import deferred_call

class NIScopeInstrument(Instrument):

    DeviceName = Member()

    data = Member()  # holds acquired data until they are written
    mode = Str('experiment')  # experiment vs. video
    analysis = Member()  # holds a link to the GUI display
    
    scope = Member()

    TrigSlope = Int(0)
    TrigMode = Int(0)
    TrigSource = Int(2)
    TrigLevel = Member()
    TrigDelay = Member()
    
    HorizScale = Int(0)
    HorizRecordLength = Member()
    
    Chan0VertScale = Int(0)
    Chan0Coupling = Int(0)
    Chan0Impedance = Int(0)
    Chan0Atten = Int(0)
    Chan0Offset = Member()
    
    Chan1VertScale = Int(0)
    Chan1Coupling = Int(0)
    Chan1Impedance = Int(0)
    Chan1Atten = Int(0)
    Chan1Offset = Member()
    
    voltageranges = [2.5,2.0,1.0,0.50,0.20,0.10]
    if niScopeImported:
        couplings = [COUPLING.DC, COUPLING.AC, COUPLING.GND, COUPLING.HF_REJECT, COUPLING.AC_PLUS_HF_REJECT]
        triggerSources = ['0', '1', TRIGGER_SOURCE.EXTERNAL, TRIGGER_SOURCE.IMMEDIATE]
        triggerSlopes = [SLOPE.POSITIVE, SLOPE.NEGATIVE]
    else:
        couplings = range(20)
        triggerSources = range(20)
        triggerSlopes = range(20)
    attens = [1,10]
    
    
    

    def __init__(self, name, experiment, description=''):
        super(NIScopeInstrument, self).__init__(name, experiment, description)
        self.DeviceName = StrProp('DeviceName', experiment, 'NI Device Name', 'Dev0')
        self.TrigLevel = FloatProp('TrigLevel', experiment, 'Trigger Level (V)', '0')
        self.TrigDelay = FloatProp('TrigDelay', experiment, 'Trigger Delay (s)', '0')
        self.HorizRecordLength = IntProp('HorizRecordLength', experiment, 'Number of points to take per trigger', '0')
        self.Chan0Offset = FloatProp('Chan0Offset', experiment, 'CH0 Offset (V)', '0')
        self.Chan1Offset = FloatProp('Chan1Offset', experiment, 'CH1 Offset (V)', '0')
        self.properties += ['DeviceName','TrigLevel','TrigDelay','HorizRecordLength','Chan0Offset',
                            'Chan1Offset','Chan1Atten','Chan1Impedance','Chan1Coupling','Chan1VertScale',
                            'Chan0Atten','Chan0Impedance','Chan0Coupling','Chan0VertScale',
                            'HorizScale','TrigSource','TrigMode','TrigSlope']

    def initialize(self):
        try:
            self.scope = niScope.Scope(resourceName=self.DeviceName.value)
        except Exception as e:
            logger.error("Failed to initialize niScope (name: {}). Exception: {}".format(self.DeviceName.value,e))
            raise PauseError
        self.isInitialized = True

    def start(self):
        self.scope.InitiateAcquisition()
        self.isDone = True

    def update(self):
        if self.enable:
            if not self.isInitialized:
                self.initialize()
                
            samplerate = self.getSampleRate()
            self.scope.ConfigureHorizontalTiming(numPts=self.HorizRecordLength.value,sampleRate=samplerate)
            
            chanList = "0:1"
            self.scope.ConfigureChanCharacteristics(chanList,impedance,maxFrequency)

            self.scope.ConfigureVertical(channelList='0',voltageRange=self.voltageranges[self.Chan0VertScale],offset=self.Chan0Offset.value,coupling=self.couplings[self.Chan0Coupling],probeAttenuation=self.attens[self.Chan0Atten])
            
            self.scope.ConfigureVertical(channelList='1',voltageRange=self.voltageranges[self.Chan0VertScale],offset=self.Chan1Offset.value,coupling=self.couplings[self.Chan1Coupling],probeAttenuation=self.attens[self.Chan0Atten])
            
            self.scope.ConfigureTrigger("Edge",self.triggerSources[self.TrigSource],self.TrigLevel.value,self.triggerSlopes[self.TrigSlope],COUPLING.DC,0,self.TrigDelay.value)
            

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
 
        #(do some config shit here)

        self.StartAcquisition()

        # run the video loop in a new thread
        self.start_video_thread()


    def start_video_thread(self):
        while self.mode == 'video':
            if self.getData():
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
            self.data = scope.Fetch(channelList='0,1')

    def writeResults(self, hdf5):
        """Overwritten from Instrument.  This function is called by the experiment after
        data acquisition to write the obtained images to hdf5 file."""
        if self.enable:
            try:
                hdf5['NIScope_{}'.format(self.DeviceName.value)] = self.data
            except Exception as e:
                logger.error('in NIScope.writeResults:\n{}'.format(e))
                raise PauseError

    def getLimits(self):
        return self.HorizScale, self.VertScale  #How to set vert scale?


class NIScopeViewer(AnalysisWithFigure):
    """Plots the currently incoming shot"""
    data = Member()
    update_lock = Bool(False)
    artist = Member()
    mycam=Member()

    maxPixel0 = Int(0)
    meanPixel0 = Int(0)
    maxPixel1 = Int(0)
    meanPixel1 = Int(0)

    def __init__(self, name, experiment, description,camera):
        super(NIScopeViewer, self).__init__(name, experiment, description)
        self.properties += []
        self.mycam=camera

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        self.data = []
        if 'data/NIScope_{}'.format(self.mycam.DeviceName.value) in measurementResults:
            #for each image
            self.data = measurementResults['data/NIScope_{}'.format(self.mycam.DeviceName.value)]
        self.updateFigure()  # only update figure if image was loaded

    @observe('shot')
    def reload(self, change):
        self.updateFigure()

    def updateFigure(self):
        if not self.update_lock and (self.mycam.mode != 'video'):
            try:
                self.update_lock = True
                try:
                    xlimit, ylimit = self.mycam.getLimits()
                    limits = True
                except:
                    limits = False
                fig = self.backFigure
                fig.clf()

                if (self.data is not None):
                    ax = fig.add_subplot(111)
                    
                    #data format: 0: x values, 1: CH0 y, 2: CH1 y
                    ax.plot(self.data[0],self.data[1],'b-')
                    ax.set_xlabel('Time (s)')
                    ax.set_ylabel('CH0 (V)')
                    ax.set_title('Title')
                    ax.tick_params('y',colors='b')

                    ax.set_ylim(-self.mycam.voltageranges[self.mycam.Chan0VertScale]+self.mycam.Chan0Offset, self.mycam.voltageranges[self.mycam.Chan0VertScale]+self.mycam.Chan0Offset)
                        
                    ax2 = ax.twinx()
                    ax2.plot(self.data[0],self.data[2],'r-')
                    ax2.set_ylabel('CH1 (V)')
                    ax2.tick_params('y',colors='r')
                    
                    ax2.set_ylim(-self.mycam.voltageranges[self.mycam.Chan1VertScale]+self.mycam.Chan1Offset, self.mycam.voltageranges[self.mycam.Chan1VertScale]+self.mycam.Chan1Offset)

                    self.maxPixel0 = numpy.max(self.data[1])
                    self.meanPixel0 = numpy.mean(self.data[1])
                    self.maxPixel1 = numpy.max(self.data[2])
                    self.meanPixel1 = numpy.mean(self.data[2])
                super(NIScopeViewer, self).updateFigure()
            except Exception as e:
                logger.warning('Problem in NIScopeViewer.updateFigure()\n:{}'.format(e))
            finally:
                self.update_lock = False

    def setup_video(self, data):
        """Use this method to connect the analysis figure to an array that will be rapidly updated
        in video mode."""
        self.data = data
        fig = self.backFigure
        fig.clf()
        ax = fig.add_subplot(111)

        self.artist = ax.plot(data)
        super(NIScopeViewer, self).updateFigure()

    def redraw_video(self):
        """First update self.data using NIScope methods, then redraw screen using this."""
        if (self.mycam.autoscale):
            self.artist.autoscale()
        else:
            self.artist.set_data(self.data)
        deferred_call(self.figure.canvas.draw)
        self.maxPixel0 = numpy.max(self.data[1])
        self.meanPixel0 = numpy.mean(self.data[1])
        self.maxPixel1 = numpy.max(self.data[2])
        self.meanPixel1 = numpy.mean(self.data[2])


class NIScope(Instrument):
    scope = Member()
    analysis = Member()

    def __init__(self, name, experiment, description=''):
        super(NIScope, self).__init__(name, experiment, description)
        self.scope = NIScopeInstrument('Scope{}'.format(name),experiment,'NIScope')
        self.analysis = NIScopeViewer('Viewer{}'.format(name),experiment,'NIScope Viewer',self.scope)
        self.properties += ['scope','analysis']

    def evaluate(self):
        self.scope.evaluate()


class NIScopes(Instrument,Analysis):
    version = '2016.06.02'
    motors = Member()
    dll = Member()

    def __init__(self, name, experiment, description=''):
        super(NIScopes, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual NIScopes', listElementType=NIScope,
                               listElementName='motor')
        self.properties += ['version', 'motors']
        self.initialize(True)

    def initializecameras(self):
        try:
            for i in self.motors:
                if i.scope.enable:
                    msg = i.scope.initialize()
        except Exception as e:
            logger.error('Problem initializing NIScope:\n{}\n{}\n'.format(msg,e))
            self.isInitialized = False
            raise PauseError

    def initialize(self, cameras=False):
        msg=''
        if niScopeImported:
            self.enable = True
            self.isInitialized = True
        else:
            self.enable = False
            self.isInitialized = False
            return
        if (cameras):
            self.initializecameras()

    def start(self):
        msg = ''
        try:
            for i in self.motors:
                if i.scope.enable:
                    msg = i.scope.start()
        except Exception as e:
            logger.error('Problem starting NIScope:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

        self.isDone = True




    def update(self):
        msg = ''
        try:
            for i in self.motors:
                if i.scope.enable:
                    msg = i.scope.update()
        except Exception as e:
            logger.error('Problem updating NIScope:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def evaluate(self):
        msg = ''
        try:
            for i in self.motors:
                msg = i.evaluate()
        except Exception as e:
            logger.error('Problem evaluating NIScope:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def writeResults(self, hdf5):
        msg = ''
        try:
            for i in self.motors:
                if i.scope.enable:
                    msg = i.scope.writeResults(hdf5)
        except Exception as e:
            logger.error('Problem writing NIScope data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError

    def acquire_data(self):
        msg = ''
        try:
            for i in self.motors:
                if i.scope.enable:
                    logger.debug( "Acquiring data from camera {}".format(i.scope.DeviceName.value))
                    msg = i.scope.acquire_data()
        except Exception as e:
            logger.error('Problem acquiring NIScope data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError


    def analyzeMeasurement(self,measurementresults,iterationresults,hdf5):
        msg = ''
        try:
            for i in self.motors:
                if i.scope.enable:
                    logger.debug("Displaying data from camera {}".format(i.scope.DeviceName.value))
                    msg = i.analysis.analyzeMeasurement(measurementresults,iterationresults,hdf5)
        except Exception as e:
            logger.error('Problem displaying NIScope data:\n{}\n{}\n'.format(msg, e))
            self.isInitialized = False
            raise PauseError
        return 0

