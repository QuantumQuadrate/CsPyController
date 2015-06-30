from __future__ import division

"""
conex.py

part of the CsPyController package for AQuA experiment control by Martin Lichtman

Handles sending global variable updates to the Newport CONEX-CC translation stage.
This python code sends commands via TCP to a server running in C#, also in this package.
The C# server then uses the .NET assembly provided by Newport to talk to the CONEX-CC driver.

created = 2015.06.29
modified >= 2015.06.29
"""

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Str, Member, Int
from instrument_property import Prop, FloatProp, IntProp, ListProp, BoolProp, StrProp
from cs_instruments import Instrument
import TCP
from cs_errors import PauseError
import time

class Conex(Prop):
    SetPos = Member()
    Vel = Member()
    enableVel = Bool()
    IDString = Member()

    def __init__(self, name, experiment, description=''):
        super(Conex, self).__init__(name, experiment, description)
        self.IDString = StrProp('IDString', experiment, 'Instrument Key','0')
        self.SetPos = FloatProp('SetPos', experiment, 'Set position (mm)','0')
        #self.enableVel = BoolProp('enableVel', experiment, '', '0')
        self.Vel = FloatProp('Vel', experiment, 'Velocity (mm/s)','0')
        self.properties += ['SetPos', 'enableVel', 'Vel']

        
    def initialize(self):
        return 'Init,{}'.format(self.IDString.value)
    
    def update(self):
        if (self.enableVel == False):
            return 'SetPosition,{}'.format(self.SetPos.value)
        else:
            return 'SetPositionVelocity,{},{}'.format(self.SetPos.value,self.Vel.value)


class Conexes(Instrument):
    version = '2015.06.22'
    IP = Str()
    port = Int()
    motors = Member()
    socket = Member()

    def __init__(self, name, experiment, description=''):
        super(Conexes, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual CONEX-CC stages', listElementType=Conex,
                               listElementName='motor')
        self.properties += ['version', 'IP', 'port', 'motors']

    def initialize(self):
        """Open the TCP socket"""
        if self.enable:
            self.socket = TCP.CsClientSock(self.IP, self.port)
            try:
                for i in self.motors:
                    msg = i.initialize()
                    self.socket.sendmsg(msg)
                    returnedmessage = self.socket.receive()
                    if (returnedmessage != "Success"):
                        logger.error('Problem initializing Conex: \n{}\n'.format(returnedmessage))
                        self.isInitialized = False
                        return PauseError
            except Exception as e:
                logger.error('Problem initializing Conex: \n{}\n{}\n'.format(msg,e))
                self.isInitialized = False
                return PauseError
            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True

    def update(self):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in self.motors:
                    msg = i.update()
                    # send update to the conex server
                    self.socket.sendmsg(msg)
                    self.socket.sendmsg("GetPosition")
                    returnedmessage = self.socket.receive()
                    curPos = float(returnedmessage)
                    while(i.SetPos.Value - curPos > .01)
                        time.sleep(0.1)
                        self.socket.sendmsg("GetPosition")
                        returnedmessage = self.socket.receive()
                        curPos = float(returnedmessage)
            except Exception as e:
                logger.error('Problem setting Conex positions, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError
