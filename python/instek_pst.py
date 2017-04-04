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
from instrument_property import Prop, IntProp, ListProp, FloatProp, StrProp
from cs_instruments import Instrument
import serial
from cs_errors import PauseError

class InstekPST(Prop):
    serial_number = Str()
    com_port = Member()
    tracking = Member()
    isInitialized = Bool(False)
    #num_chans = Int(3)           #TODO: Implement variable number of channels...
    voltage_setpoint_1 = Member()
    current_setpoint_1 = Member()
    voltage_setpoint_2 = Member()
    current_setpoint_2 = Member()
    voltage_setpoint_3 = Member()
    current_setpoint_3 = Member()
    actual_voltage_1 = Str()
    actual_current_1 = Str()
    actual_voltage_2 = Str()
    actual_current_2 = Str()
    actual_voltage_3 = Str()
    actual_current_3 = Str()
    ser = Member()

    def __init__(self, name, experiment, description=''):
        super(InstekPST, self).__init__(name, experiment, description)
        self.com_port = StrProp('com_port', experiment, 'Communications port of PST','0')
        self.tracking = IntProp('tracking', experiment, 'Tracking Mode (0 Independent; 1 Parallel; 2 Series)','0')
        #self.num_chans = IntProp('num_chans', experiment, 'Number of channels','0')
        self.voltage_setpoint_1 = FloatProp('voltage_setpoint_1', experiment, 'Voltage Setpoint for Channel 1','0')
        self.current_setpoint_1 = FloatProp('current_setpoint_1', experiment, 'Current Setpoint for Channel 1','0')
        self.voltage_setpoint_2 = FloatProp('voltage_setpoint_2', experiment, 'Voltage Setpoint for Channel 2','0')
        self.current_setpoint_2 = FloatProp('current_setpoint_2', experiment, 'Current Setpoint for Channel 2','0')
        self.voltage_setpoint_3 = FloatProp('voltage_setpoint_3', experiment, 'Voltage Setpoint for Channel 3','0')
        self.current_setpoint_3 = FloatProp('current_setpoint_3', experiment, 'Current Setpoint for Channel 3','0')
        self.properties += ['com_port', 'serial_number', 'tracking',
                            'voltage_setpoint_1', 'current_setpoint_1', 'voltage_setpoint_2', 'current_setpoint_2',
                            'voltage_setpoint_3', 'current_setpoint_3', 'actual_voltage_1', 'actual_current_1',
                            'actual_voltage_2', 'actual_current_2', 'actual_voltage_3', 'actual_current_3',
                            ]
    
    def initialize(self):
        self.ser = serial.Serial()
        self.ser.port = self.com_port.value
        self.ser.baudrate = 9600
        self.ser.timeout = 1
        try:
            self.ser.open()
            self.isInitialized = True
        except serial.SerialException, e:
            logger.error("Instek PST initialize: Could not open serial port %s: %s\n" % (self.ser.portstr, e))
            self.isInitialized = False
            raise PauseError

    def send_voltage_current(self,chan,voltage,current):
        self.ser.write("CHAN{}:VOLT {};CURR {}\n".format(chan,voltage,current))
        return
    
    def get_serial_number(self):   #issue "*idn?\n" to PST to get serial number
        self.ser.write("*idn?\n")
        self.serial_number = self.ser.readline()
        return
        
    def enable_output(self):
        self.ser.write(":OUTP:STAT 1\n")
        return
        
    def test_output(self):
        self.ser.write(":OUTP:STAT ?\n")
        return bool(int(self.ser.readline()))
        
    def get_actual_voltage_current(self,chan):
        self.ser.write("CHAN{}:MEAS:VOLT ?\n".format(chan))
        voltage = self.ser.readline()
        self.ser.write("CHAN{}:MEAS:CURR ?\n".format(chan))
        current = self.ser.readline()
        return voltage, current

    def measure_all_channels(self): 
        self.actual_voltage_1, self.actual_current_1 = self.get_actual_voltage_current(1)
        self.actual_voltage_2, self.actual_current_2 = self.get_actual_voltage_current(2)
        self.actual_voltage_3, self.actual_current_3 = self.get_actual_voltage_current(3)
        return
        
        
    def update(self):
        if self.isInitialized == False:
            self.initialize()
        #send voltages and currents
        #for chan in range(1, self.num_chans.value):
        self.send_voltage_current(1,self.voltage_setpoint_1.value,self.current_setpoint_1.value)
        self.send_voltage_current(2,self.voltage_setpoint_2.value,self.current_setpoint_2.value)
        self.send_voltage_current(3,self.voltage_setpoint_3.value,self.current_setpoint_3.value)
        #pause?
        #read actual voltage
        #read actual current
        #for chan in range(1, self.num_chans.value):
        
        self.measure_all_channels()
        return
        
        
    def set_tracking(self):
        if (self.tracking.value == 0 or self.tracking.value == 1 or self.tracking.value == 2):
            self.ser.write(":OUTP:COUP:TRAC {}\n".format(self.tracking.value))
        else:
            logger.error("Instek PST tracking mode must be 0 (independent), 1 (parallel), or 2 (series). Current value: {}".format(self.tracking.value))
            raise PauseError

    def get_tracking(self):
        self.ser.write(":OUTP:COUP:TRAC ?\n")
        return int(self.ser.readline())

class InstekPSTs(Instrument):
    version = '2015.07.09'
    motors = Member()

    def __init__(self, name, experiment, description=''):
        super(InstekPSTs, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual PST power supplies', listElementType=InstekPST,
                               listElementName='PST')
        self.properties += ['version', 'motors']

    def preExperiment(self, hdf5):
        """Open the TCP socket"""
        if self.enable:
            for i in self.motors:
                #initialize serial connection to each power supply
                i.initialize()
                #check connection by requesting serial number
                i.get_serial_number()
            
            
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
                    if (i.get_tracking() != i.tracking.value):
                        i.set_tracking()
            except Exception as e:
                logger.error('Problem updating current/voltage for Instek PST:\n{}\n{}\n'.format(msg, e))
                self.isInitialized = False
                raise PauseError
                
                
    def postMeasurement(self, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        if self.enable:
            for i in self.motors:
                i.measure_all_channels()
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self,hdf5):
        return
