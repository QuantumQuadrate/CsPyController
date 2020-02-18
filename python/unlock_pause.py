""" Module to pause the experiment if the Raspberry Pi detects the laser lock dropped
"""
__author__ = 'Aquarius'
import socket
from atom.api import Bool, Member, Float
from instrument_property import IntProp, FloatProp, StrProp
from cs_instruments import Instrument
from analysis import Analysis
from cs_errors import PauseError
import logging
logger = logging.getLogger(__name__)

class UnlockMonitor(Instrument, Analysis):
    version = '2017.04.03'
    IP = Member()
    Port = Member()
    Threshold = Member()
    locked_brightness = Float(0.0)
    unlocked_brightness = Float(0.0)
    s = Member()
    paused = Bool(False)

    def __init__(self, name, experiment, description=''):
        super(UnlockMonitor, self).__init__(name, experiment, description)
        self.IP = StrProp('IP', experiment, 'IP Address of Raspberry Pi', '10.141.196.160')
        self.Port = IntProp('Port', experiment, 'Port', '50007')
        self.Threshold = FloatProp('Threshold', experiment, 'Threshold for locked/unlocked', '30')
        self.properties += ['version', 'IP', 'Port', 'Threshold']

    # lock_flag is 0 for unlocked, 1 for locked
    def get_brightness(self, lock_flag):
        try:
            s = self.open_connection(5, True)
        except Exception as e:
            logger.error('Connection to Raspberry Pi failed. Error {}'.format(e))
            raise PauseError

        s.sendall('Brightness')
        brightness = float(s.recv(1024))
        self.close_connection(s)

        if lock_flag == 0:
            self.unlocked_brightness = brightness
        else:
            self.locked_brightness = brightness
        return

    def open_connection(self, timeout, block):
        logger.info("Opening connection")
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((self.IP.value, self.Port.value))
        s.settimeout(timeout)
        s.setblocking(block)
        return s

    def close_connection(self, s):
        s.close()
        return

    def start(self):
        self.isDone = True

    def preExperiment(self, hdf5):
        if self.enable:
            try:
                self.s = self.open_connection(None, False)
            except Exception as e:
                logger.error("Somethin' done went wrong: {}".format(e))
                raise PauseError
            self.s.sendall('%f' % self.Threshold.value)
        return

    #paused = Bool(False) # why is this here? MFE
    def analyzeMeasurement(self,measurementresults,iterationresults,hdf5):
        if self.enable:
            if self.paused:
                self.s.sendall('Experiment Resumed')
                self.paused = False
            try:
                data = self.s.recv(1024)
                if data is not None:
                    self.experiment.pause_now()
                    self.paused = True
            except Exception as e:
                pass
        return

    def postExperiment(self, hdf5):
        if self.enable:
            self.s.sendall('Experiment Finished')
            self.close_connection(self.s)
        return

    def stop(self):
        if self.enable:
            try:
                # Required to be twice if halted while lock is broken
                self.s.sendall("Experiment Finished")
                self.s.sendall("Experiment Finished")
            except:
                pass
            try:
                self.close_connection(self.s)
            except Exception as e:
                pass
