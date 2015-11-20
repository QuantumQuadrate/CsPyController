from __future__ import division

"""
instek_pst.py

part of the CsPyController package for AQuA experiment control by Martin Lichtman

Handles sending commands to Instek PST power supplies over RS232.

created = 2015.07.09
modified >= 2015.07.09
"""

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Str, Member, Int, Float
from instrument_property import Prop, IntProp, ListProp, FloatProp, StrProp, BoolProp
from cs_instruments import Instrument
import serial
from cs_errors import PauseError

from ctypes import *
import os

class Vaunix(Prop):
    isInitialized = Bool(False)
    ID = Int()
    va = Member()
    
    frequency = Member()
    power = Member()
    pulsewidth = Member()
    pulserep = Member()
    pulseenable = Bool()
    startfreq = Member()
    endfreq = Member()
    sweeptime = Member()
    
    sweepmode = Bool()
    sweeptype = Bool()
    sweepenable = Bool()
    sweepdir = Bool()
    internalref = Bool()
    useexternalmod = Bool()
    rfonoff = Bool()
    
    maxPower = Int()
    

    def __init__(self, name, experiment, description=''):
        super(Vaunix, self).__init__(name, experiment, description)
        self.frequency = FloatProp('Frequency', experiment, 'Frequency (MHz)', '0')
        self.power = FloatProp('Power', experiment, 'Power (dBm)', '0')
        self.pulsewidth = FloatProp('PulseWidth', experiment, 'Pulse Width (us)', '0')
        self.pulserep = FloatProp('PulseRep', experiment, 'Pulse Rep Time (us)', '0')
        self.startfreq = FloatProp('StartFreq', experiment, 'Start Frequency (MHz)', '0')
        self.endfreq = FloatProp('EndFreq', experiment, 'End Frequency (MHz)', '0')
        self.sweeptime = IntProp('SweepTime', experiment, 'Sweep Time (ms)', '0')
        self.properties += ['ID', 'frequency','power','pulsewidth','pulserep','pulseenable','startfreq','endfreq','sweeptime',
                            'sweepmode', 'sweeptype', 'sweepdir', 'sweepenable', 'internalref', 'useexternalmod', 'rfonoff', 'maxPower']
    
    def initialize(self,va):
        self.va = va
        self.maxPower = self.va.fnLMS_GetMaxPwr(self.ID)
        return
    
    def freq_unit(self,val):
        return int(val*10000)
    
    def power_unit(self,value):
        return int((self.maxPower - value)/0.25)
        
    def update(self):
        #print "Setting Frequency to {}x10 Hz".format(self.freq_unit(self.frequency.value))
        self.va.fnLMS_SetFrequency(self.ID, self.freq_unit(self.frequency.value))
        #print "Setting Power Level to {} dBm. Max Power {} dBm.".format(self.power.value, self.maxPower)
        self.va.fnLMS_SetPowerLevel(self.ID, self.power_unit(self.power.value))
        #print "Setting Start Frequency to {}x10Hz".format(self.freq_unit(self.startfreq.value))
        self.va.fnLMS_SetStartFrequency(self.ID, self.freq_unit(self.startfreq.value))
        #print "Setting End Frequency to {}x10Hz".format(self.freq_unit(self.endfreq.value))
        self.va.fnLMS_SetEndFrequency(self.ID, self.freq_unit(self.endfreq.value))
        
        self.va.fnLMS_SetSweepTime(self.ID, self.sweeptime.value)
        
        self.va.fnLMS_SetUseInternalRef(self.ID, self.internalref)  #True: internal ref, False: external ref
        
        self.va.fnLMS_SetSweepDirection(self.ID, self.sweepdir)
        
        self.va.fnLMS_SetSweepMode(self.ID, self.sweepmode)  #True: Repeat Sweep, False: Sweep Once
        
        self.va.fnLMS_SetSweepType(self.ID, self.sweeptype)  #True: Bidirectional Sweep, False: Unidirectional Sweep
        #print "Setting FastPulsedOutput"
        self.va.fnLMS_SetFastPulsedOutput(self.ID, c_float(self.pulsewidth.value*1e-6), c_float(self.pulserep.value*1e-6), self.pulseenable)
        #print "SetUseExternalPulseMod"
        self.va.fnLMS_SetUseExternalPulseMod(self.ID, self.useexternalmod)
        #print "SetRFOn"
        self.va.fnLMS_SetRFOn(self.ID, self.rfonoff)
        self.va.fnLMS_StartSweep(self.ID, self.sweepenable)
        return
        
        

class Vaunixs(Instrument):
    version = '2015.11.19'
    motors = Member()
    isInitialized = Bool(False)
    va = Member()
    
    testMode = Bool(True)
	
    def __init__(self, name, experiment, description=''):
        super(Vaunixs, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Vaunix signal generators', listElementType=Vaunix,
                               listElementName='Vaunix')
        self.properties += ['version', 'motors']
        num = self.initialize()
        self.motors.length = num
        self.motors.refreshGUI()

    #Initialize: loads and initializes DLL
    def initialize(self):
        CDLL_file = "vaunix/VNX_fmsynth.dll"
        self.va = CDLL(CDLL_file)
        if (self.testMode):
            logger.warning("Warning: Vaunix in test mode. Set testMode=False in vaunix.py to turn off test mode.")
        self.va.fnLMS_SetTestMode(self.testMode)   #Test mode... this needs to be set False for actual run. Do not remove this command (default setting is True).
        self.isInitialized = True
        num = self.detect_generators()
        return num
		
    def preExperiment(self, hdf5):
        if self.enable:
            if (not self.isInitialized):
                self.initialize()
            for i in self.motors:
                #initialize serial connection to each power supply
                i.initialize(self.va)
            
            
            self.isInitialized = True

    def preIteration(self, iterationresults, hdf5):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in self.motors:
                    i.update()
            except Exception as e:
                logger.error('Problem updating Vaunix:\n{}\n{}\n'.format(msg, e))
                self.isInitialized = False
                raise PauseError
                
                
    def postMeasurement(self, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self,hdf5):
        return
	
	#detect_generators: Calls DLL function to check for number of generators and their IDs.
    def detect_generators(self):
        if (not self.isInitialized):
            self.initialize()
        num=self.va.fnLMS_GetNumDevices()
        logger.debug("Number of vaunix devices detected: {}".format(num))
        while (num>len(self.motors)):
            self.motors.add()
        while (num<len(self.motors)):
            self.motors.remove(len(self.motors) - 1)
        devinfotype = c_uint*num
        devinfo = devinfotype()
        self.va.fnLMS_GetDevInfo(addressof(devinfo))
        for mn, i in enumerate(self.motors):
            i.ID = int(devinfo[mn])
        return num
