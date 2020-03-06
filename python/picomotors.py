from __future__ import division

"""
picomotors.py

part of the CsPyController package for AQuA experiment control by Martin Lichtman

Handles sending position commands to Newport/New Focus Picomotors
This python code sends commands via TCP to a server running in C#, also in this package.
The C# server then uses the .NET assembly provided by Newport to talk to the 8742 Picomotor driver.

created = 2014.07.09
modified >= 2014.07.09
"""

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Str, Member, Int
from instrument_property import Prop, IntProp, ListProp, Float
from cs_instruments import Instrument
import TCP
from cs_errors import PauseError

class Picomotor(Prop):
    # must keep track of position changes and send only difference
    serial_number = Str()
    motor_number = Str()
    desired_position = Member()
    current_position = Int()
    max_angle_error = Float(0)  # necessary so I don't have to define a new enaml container

    def __init__(self, name, experiment, description=''):
        super(Picomotor, self).__init__(name, experiment, description)
        self.desired_position = IntProp('desired_position', experiment, 'the desired position','0')
        self.properties += ['serial_number', 'motor_number', 'desired_position', 'max_angle_error']
        self.current_position = self.desired_position.value

    def update(self):
        # calculate relative move necessary
        relative_move = self.desired_position.value - self.current_position
        return '{},{},{}'.format(serial_number, motor_number, relative_move)


class Picomotors(Instrument):
    version = '2014.07.09'
    IP = Str()
    port = Int()
    motors = Member()
    socket = Member()

    def __init__(self, name, experiment, description=''):
        super(Picomotors, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual picomotors', listElementType=Picomotor,
                               listElementName='motor')
        self.properties += ['version', 'IP', 'port', 'motors']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.socket = TCP.CsClientSock(self.IP, self.port)

            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in motors:
                    # get the serial number, motor, and position from each motor
                    msg = i.update()
                    # send it to the picomotor server
                    self.socket.sendmsg(msg)
            except Exception as e:
                logger.error('Problem setting Picomotor position, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError
