"""pypico.py
Part of the AQuA Cesium Controller software package

author=Matthew Ebert
created=2017-05-25
modified=2018-07-07 by Minho Kwon to solve unreliable hardware operation taken care by software.

This instrument communicates with the pypcio server running in another process
using zmq and SCPI commands.
The pypico server abstracts the closed loop control of picomotor positioners.
"""

__author__ = 'Matthew Ebert'
import logging
logger = logging.getLogger(__name__)

from cs_instruments import Instrument
from instrument_property import ListProp, FloatProp
import zmq
from picomotors import Picomotor
from cs_errors import PauseError

from atom.api import Float, Str, Int, Member, Bool
import random

def is_error_msg(msg):
    error_str = "Error : "
    return msg[:len(error_str)] == error_str


class PyPicomotor(Picomotor):
    current_position = Float()
    max_angle_error = Float(0.2)  # maximum error to accept without trying to correct


    def __init__(self, name, experiment, description=''):
        super(PyPicomotor, self).__init__(name, experiment, description)
        self.desired_position = FloatProp('desired_position', experiment, 'the desired position','0')
        self.properties += ['current_position']

    def readPosition(self, socket):
        socket.send('READ:MOT{}'.format(self.motor_number))
        message = socket.recv()
        if is_error_msg(message):
            no_error = False
            msg = 'When reading picomotor angle, recieved error msg: `{}`'
            logger.warn(msg.format(message))
            raise PauseError
        else:
            try:
                self.current_position = float(message)
            except Exception:
                msg = 'Exception when attempting to read motor `{}` position.'
                logger.exception(msg.format(self.motor_number))

    def update(self,settler=False):
        '''generates command to move to desired position. If no movement is
        necessary then it returns an empty string
        '''
        diff = (self.desired_position.value - self.current_position)
        if abs(diff) < self.max_angle_error:
            return ''

        if settler:
            settling_offset=1
        else:
            settling_offset=0

        cmd = 'MOVE:ABS:MOT{}:{} DEG'.format(
            self.motor_number,
            self.desired_position.value-settling_offset # For settling purpose, we will not make a movement.
        )
        return cmd

class PyPicoServer(Instrument):
    version = '2018.07.07'
    IP = Str('127.0.0.1')
    port = Int(5000)
    motors = Member()
    context = Member()
    socket = Member()
    timeout = Int(20000)  # default is 10 secs, since motor movement can take a while
    enable_measurement = Bool()
    enable_iteration = Bool()
    enable_movement = Bool()


    def __init__(self, name, experiment, description=''):
        super(PyPicoServer, self).__init__(name, experiment, description)
        self.motors = ListProp(
            'motors',
            experiment,
            'A list of individual picomotors',
            listElementType=PyPicomotor,
            listElementName='motor'
        )
        self.properties += [
            'version', 'IP', 'port', 'motors', 'enable_measurement',
            'enable_iteration', 'enable_movement', 'timeout'
        ]

    def initialize(self):
		# Reading position happens every measurement if they are both enabled.
        if self.enable and self.enable_measurement:
        #"""Open the zmq socket"""
            self.opensocket()
            try:
                self.readPositions()# read motor positions from server
            except Exception:
                logger.exception('Problem initializing sever communication in pypico.')
        if self.enable and self.enable_measurement and self.enable_movement:
            self.moveit()

    def opensocket(self):
		self.context = zmq.Context()
		self.socket = self.context.socket(zmq.REQ)
		# set socket timeout in ms
		self.socket.RCVTIMEO = self.timeout
		self.socket.connect('tcp://{}:{}'.format(self.IP, self.port))

    def readPositions(self):
        '''Read the position of all picomotors in degrees'''
        logger.info('Reading picomotor positions...')
        request = "READ:MOT{}" # READ:MOTor#
        no_error = True
        i = 0
        for m in self.motors:
            m.readPosition(self.socket)

    def move_motor(self, m, cmd):
        self.socket.send(cmd)
        message = self.socket.recv()
        if is_error_msg(message):
            msg = 'When moving picomotor `{}`, recieved error msg: `{}`'
            logger.warn(msg.format(m.motor_number, message))
            # TODO: check to see if the error is because it didnt
            # meet the setpoint, within the specified error
            # if that is the case try again at least once
            raise PauseError
        else:
            m.readPosition(self.socket)
            move_error = m.desired_position.value - m.current_position
            msg = (
                'Motor `{}` moved to position `{}` with no error.'
                ' Positional error is `{}` DEG.'
            )
            logger.info(msg.format(
                m.motor_number,
                m.current_position,
        move_error
            ))
        done = True
        if abs(move_error) > m.max_angle_error:
            done = False
        return done

    def moveit(self):
        msg = ''
        list_of_motors=[]
        for m in self.motors:
            list_of_motors.append(m)
        random.shuffle(list_of_motors)
        print list_of_motors
        try:
            for m in list_of_motors:
                # the motor class can make up its own commands
                # As an initial attempt, we will make partial correction, leaving only forward correction.
                cmd = m.update(settler=True)
                if cmd: # '' is falsy
                    for trial in range(2):
                        if self.move_motor(m, cmd):
                            logger.info("Settling trial")
                            break
            for m in list_of_motors:
                # the motor class can make up its own commands
                cmd = m.update(settler=False)
                if cmd: # '' is falsy
                    for trial in range(2):
                        if self.move_motor(m, cmd):
                            logger.info("Final approach")
                            break
                        else:
                            logger.info("Missed trying again")
        except Exception as e:
            logger.exception('Problem setting Picomotor position, closing socket.')
            self.socket.close()
            self.isInitialized = False
            raise PauseError

    def update(self):
        """Every iteration, send the motors updated positions.
        """
        if self.enable and self.enable_iteration:
            self.opensocket()
            try:
                self.readPositions()# read motor positions from server
            except Exception:
                logger.exception('Problem initializing sever communication in pypico.')

        if self.enable and self.enable_iteration and self.enable_movement:
            self.moveit()
