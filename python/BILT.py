"""bilt_voltage.py
   Part of the AQuA Cesium Controller software package

   created=2017-06-08

   This code communicates with the Bilt chassis. The various cards (e.g. low 
   noise voltage sources) are imported, so any chassis configuration can be
   used. It uses SCPI commands through PyVISA, which is a backend that wraps the
   National Instruments VISA library. NI-VISA must be installed to use PyVISA. 
   

   """

import logging
logger = logging.getLogger(__name__)
from cs_errors import PauseError

import time
import socket
from atom.api import Int, Str, Member
from instrument_property import Prop, FloatProp, ListProp
from cs_instruments import Instrument


class BILTcard(Prop):
    # must keep track of voltage changes
    chassis_card_number = Str()
    channel_number = Str()
    desired_voltage = Member()


    def __init__(self, name, experiment, description=''):
        super(BILTcard, self).__init__(name, experiment, description)
        self.desired_voltage = FloatProp('desired_voltage', experiment, 'the desired voltage','0')
        self.properties += ['chassis_card_number', 'channel_number', 'desired_voltage']

    def update(self):
        # return the new voltage value
        return 'i{}; c{}; volt {}\n'.format(self.chassis_card_number, self.channel_number, self.desired_voltage.value)

class BILTcards(Instrument):
    version = '2017.07.25'
    channels = Member()
    port = Int()
    socket = Member()
    IP = Str()

    def __init__(self, name, experiment, description=''):
        super(BILTcards, self).__init__(name, experiment, description)
        self.channels = ListProp('channels', experiment, 'A list of voltage channels', listElementType=BILTcard, listElementName='channel')        
        self.properties += ['version','IP', 'port', 'channels']


    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.isInitialized = True

    def start(self):
        self.isDone = True

    def update(self):
        """
        Every iteration, send the channels updated voltages.
        """
        if self.enable:
            msg = ''
            try:
                for i in self.channels:
                    # get the chassis slot, channel number, and voltage from each channel
                    msg = i.update()
                    # send it to the chasis  
                    self.socket = socket.socket()  
                    self.socket.connect((self.IP, self.port))
                    self.socket.send(msg)
                    time.sleep(0.2)
                    self.socket.send('meas:volt ?\n')
                    logger.info(self.socket.recv(1024))
                    self.socket.close()
                    time.sleep(0.2)
                    
            except Exception as e:
                logger.error('Problem setting BILT voltage, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError
