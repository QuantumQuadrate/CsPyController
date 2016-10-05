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
    model = Str()
    serial = Int()
    
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
    minPower = Int()
    minFreq = Int()
    maxFreq = Int()
    

    def __init__(self, name, experiment, description=''):
        super(Vaunix, self).__init__(name, experiment, description)
        self.frequency = FloatProp('Frequency', experiment, 'Frequency (MHz)', '0')
        self.power = FloatProp('Power', experiment, 'Power (dBm)', '0')
        self.pulsewidth = FloatProp('PulseWidth', experiment, 'Pulse Width (us)', '0')
        self.pulserep = FloatProp('PulseRep', experiment, 'Pulse Rep Time (us)', '0')
        self.startfreq = FloatProp('StartFreq', experiment, 'Start Frequency (MHz)', '0')
        self.endfreq = FloatProp('EndFreq', experiment, 'End Frequency (MHz)', '0')
        self.sweeptime = IntProp('SweepTime', experiment, 'Sweep Time (ms)', '0')
        self.properties += ['ID', 'model', 'serial', 'frequency','power','pulsewidth','pulserep','pulseenable','startfreq','endfreq','sweeptime',
                            'sweepmode', 'sweeptype', 'sweepdir', 'sweepenable', 'internalref', 'useexternalmod', 'rfonoff', 'maxPower']
    
    def initialize(self,va):
        self.va = va
        errcode = self.va.fnLMS_InitDevice(self.ID)
        if (errcode !=0):
            errcodereset = self.va.fnLMS_CloseDevice(self.ID)
            if (errcodereset != 0):     #if device fails to initialize, it may be because it was not closed previously. Try closing and reinitializing it.
                logger.error("Failed to initialize Vaunix device {}. Error code {}.".format(self.ID,errcode))
                raise PauseError
            errcode = self.va.fnLMS_InitDevice(self.ID)
            if (errcode != 0):
                logger.error("Failed to initialize Vaunix device {}. Error code {}.".format(self.ID,errcode))
                raise PauseError
        self.maxPower = int(self.va.fnLMS_GetMaxPwr(self.ID)/4)
        self.minPower = int(self.va.fnLMS_GetMinPwr(self.ID)/4)
        self.minFreq = int(self.va.fnLMS_GetMinFreq(self.ID))
        self.maxFreq = int(self.va.fnLMS_GetMaxFreq(self.ID))
        
        return
    
    def freq_unit(self,val):
        return int(val*100000)
    
    def power_unit(self,value):
        return int((self.maxPower - value)*4)
        
    def power_sanity_check(self,value):
        if (value < self.minPower or value > self.maxPower):
            logger.error("Vaunix device {} power ({} dBm) outside min/max range: {} dBm, {} dBm.".format(self.ID,value,self.minPower,self.maxPower))
            raise PauseError
        return

    def freq_sanity_check(self,value):
        if (value < self.minFreq or value > self.maxFreq):
            logger.error("Vaunix device {} frequency ({} x10 Hz) outside min/max range: {} x10 Hz, {} x10 Hz.".format(self.ID,value,self.minFreq,self.maxFreq))
            raise PauseError
        return        

        
    def update(self):
        if (self.rfonoff):
            self.freq_sanity_check(self.freq_unit(self.frequency.value))
            self.va.fnLMS_SetFrequency(self.ID, self.freq_unit(self.frequency.value))
            
            self.power_sanity_check(self.power.value)
            self.va.fnLMS_SetPowerLevel(self.ID, self.power_unit(self.power.value))
            
            if (self.sweepenable):
                self.freq_sanity_check(self.freq_unit(self.startfreq.value))
                self.va.fnLMS_SetStartFrequency(self.ID, self.freq_unit(self.startfreq.value))
                
                self.freq_sanity_check(self.freq_unit(self.endfreq.value))
                self.va.fnLMS_SetEndFrequency(self.ID, self.freq_unit(self.endfreq.value))
                
                self.va.fnLMS_SetSweepTime(self.ID, self.sweeptime.value)

                self.va.fnLMS_SetSweepDirection(self.ID, self.sweepdir)
                
                self.va.fnLMS_SetSweepMode(self.ID, self.sweepmode)  #True: Repeat Sweep, False: Sweep Once
                
                self.va.fnLMS_SetSweepType(self.ID, self.sweeptype)  #True: Bidirectional Sweep, False: Unidirectional Sweep
                
                self.va.fnLMS_StartSweep(self.ID, self.sweepenable)

            self.va.fnLMS_SetFastPulsedOutput(self.ID, c_float(self.pulsewidth.value*1e-6), c_float(self.pulserep.value*1e-6), self.pulseenable)

            self.va.fnLMS_SetUseExternalPulseMod(self.ID, self.useexternalmod)
            
            self.va.fnLMS_SetUseInternalRef(self.ID, self.internalref)  #True: internal ref, False: external ref
            
            self.va.fnLMS_SaveSettings(self.ID)
        
        self.va.fnLMS_SetRFOn(self.ID, self.rfonoff)
        
        self.getparams()
        return
        
    def getparams(self):
        print "Parameters for Vaunix # {}".format(self.ID)
        print "Frequency: {} MHz".format(self.va.fnLMS_GetFrequency(self.ID)/100000)
        print "Power Level: {} dBm".format(self.va.fnLMS_GetPowerLevel(self.ID)/4)
        
        

class Vaunixs(Instrument):
    version = '2015.11.19'
    motors = Member()
    isInitialized = Bool(False)
    va = Member()
    
    testMode = Bool(False)    #Test mode: Set to False for actual use.
	
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
        CDLL_file = os.path.join(os.path.dirname(__file__),"vaunix/VNX_fmsynth.dll")
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
        if (not self.isInitialized):    #test if DLL is already loaded. If not, load it.
            self.initialize()
        num=self.va.fnLMS_GetNumDevices()   #ask DLL for the number of connected devices
        logger.debug("Number of vaunix devices detected: {}".format(num))
        while (num>len(self.motors)):       #if num connected devices > number in array, add elements.
            self.motors.add()
        while (num<len(self.motors)):       #if <, subtract elements.
            self.motors.pop(self.motors.length-1)
            self.motors.length -= 1
        devinfotype = c_uint*num
        devinfo = devinfotype()
        self.va.fnLMS_GetDevInfo(addressof(devinfo))   #get device IDs
        for mn, i in enumerate(self.motors):
            i.ID = int(devinfo[mn])                    #copy device IDs to ID variable
            modnumtype = c_char*100
            modnum = modnumtype()
            self.va.fnLMS_GetModelNameA(i.ID,addressof(modnum))   #get device model names
            i.model = modnum.value
            serial = c_int()
            serial = self.va.fnLMS_GetSerialNumber(i.ID)   #get device serial numbers
            i.serial = serial
        return num
