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

from ctypes import c_int, c_double, byref, c_char_p, CDLL
import os

class Vaunix(Prop):
    isInitialized = Bool(False)
    ID = Str()
    va = Member()
    
    frequency = Member()
    power = Member()
    pulsewidth = Member()
    pulserep = Member()
    pulseenable = Bool()
    startfreq = Member()
    endfreq = Member()
    sweeptime = Member()
    
    maxPower = Float()
    

    def __init__(self, name, experiment, description=''):
        super(Vaunix, self).__init__(name, experiment, description)
        self.frequency = FloatProp('Frequency', experiment, 'Frequency (MHz)', '0')
        self.power = FloatProp('Power', experiment, 'Power (dBm)', '0')
        self.pulsewidth = FloatProp('PulseWidth', experiment, 'Pulse Width (us)', '0')
        self.pulserep = FloatProp('PulseRep', experiment, 'Pulse Rep Time (us)', '0')
        #self.pulseenable = BoolProp('PulseEnable', experiment, 'Pulse Enable', '0')
        self.startfreq = FloatProp('StartFreq', experiment, 'Start Frequency (MHz)', '0')
        self.endfreq = FloatProp('EndFreq', experiment, 'End Frequency (MHz)', '0')
        self.sweeptime = FloatProp('SweepTime', experiment, 'Sweep Time (ms)', '0')
        self.properties += ['ID', 'Frequency','Power','PulseWidth','PulseRep','PulseEnable','StartFreq','EndFreq','SweepTime'
                            ]
    
    def initialize(self,va):
        self.va = va
        self.maxPower = self.va.fnLMS_GetMaxPwr(self.ID)
        return
    
    def freq_unit(self,val):
        return int(val*10000)
    
        
    def update(self):
        self.va.fnLMS_SetFrequency(self.ID, freq_unit(self.frequency.value))
        self.va.fnLMS_SetPowerLevel(self.ID, int((self.maxPower - self.power)/0.25))
        self.va.fnLMS_SetStartFrequency(self.ID, freq_unit(self.startfreq.value))
        self.va.fnLMS_SetEndFrequency(self.ID, freq_unit(self.endfreq.value))
        self.va.fnLMS_SetSweepTime(self.ID, self.sweeptime.value)
        self.va.fnLMS_SetUseInternalRef(self.ID, True)  #True: internal ref, False: external ref
        self.va.fnLMS_SetSweepDirection(self.ID, self.sweepdir)
        self.va.fnLMS_SetSweepMode(self.ID, self.sweepmode)  #True: Repeat Sweep, False: Sweep Once
        self.va.fnLMS_SetSweepType(self.ID, self.sweeptype)  #True: Bidirectional Sweep, False: Unidirectional Sweep
        self.va.fnLMS_SetFastPulsedOutput(self.ID, self.pulsewidth*1e-6, self.pulserep*1e-6, self.pulseenable)
        
        self.va.fnLMS_SetUseExternalPulseMod(self.ID, self.useexternalmod)
        
        self.va.fnLMS_SetRFOn(self.ID, True)
        self.va.fnLMS_StartSweep(self.ID, self.sweepenable)
        return
        
        

class Vaunixs(Instrument):
    version = '2015.11.19'
    motors = Member()
    isInitialized = Bool(False)
    va = Member()
	
    def __init__(self, name, experiment, description=''):
        super(Vaunixs, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Vaunix signal generators', listElementType=Vaunix,
                               listElementName='Vaunix')
        self.properties += ['version', 'motors']

    #Initialize: loads and initializes DLL
    def initialize(self):
        CDLL_file = "VNX_fmsynth.dll"
        self.va = CDLL(CDLL_file)
        self.va.fnLDA_SetTestMode(False)
        self.detect_generators()
        self.isInitialized = True
        return
		
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
                    if i.test_output() == False:
                        i.enable_output()
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
        num=va.fnLMS_GetNumDevices()
        while (num>self.motors.len):
            self.motors.add()
        while (num<self.motors.len):
            self.motors.remove(self.motors.len - 1)
        devinfo = c_int()*num
        self.va.fnLMS_GetDevInfo(by_ref(devinfo))
        for mn, i in enumerate(self.motors):
            i.ID = devinfo[mn]
        return
