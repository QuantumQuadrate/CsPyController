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
import subprocess

class Conex(Prop):
    SetPos = Member()
    Vel = Member()
    enableVel = Bool()
    IDString = Member()
    Threshold = Member()

    def __init__(self, name, experiment, description=''):
        super(Conex, self).__init__(name, experiment, description)
        self.IDString = StrProp('IDString', experiment, 'Instrument Key','0')
        self.SetPos = FloatProp('SetPos', experiment, 'Set position (mm)','0')
        self.Vel = FloatProp('Vel', experiment, 'Velocity (mm/s)','0')
        self.Threshold = FloatProp('PositionThreshold', experiment, 'Threshold for Position (mm)','0')
        self.properties += ['SetPos', 'enableVel', 'Vel', "IDString",'PositionThreshold']

        
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

    def launchServer(self):
        subprocess.Popen(["C:\\Windows\\System32\\cmd.exe","/C","..\\csharp\\CONEX_Server\\bin\\Debug\\Ensemble Console Example CSharp.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)

    def preExperiment(self, hdf5):
        """Open the TCP socket"""
        if self.enable:
            self.socket = TCP.CsClientSock(self.IP, self.port)
            try:
                for i in self.motors:
                    msg = i.initialize()
                    self.socket.sendmsg(msg)
                    logger.debug("CONEX: Sent initialization message, waiting for response")
                    returnedmessage = self.socket.receive()
                    logger.debug("CONEX: Received response: {}".format(returnedmessage))
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


    def postMeasurement(self, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self, hdf5):
        self.socket.close()
        return

    def preIteration(self, iterationresults, hdf5):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''
            try:
                for i in self.motors:
                    msg = i.update()
                    # send update to the conex server
                    logger.debug("Conex: About to send update to CONEX server")
                    self.socket.sendmsg(msg)
                    logger.debug("Conex: Sent update to CONEX server. About to ask position")
                    self.socket.sendmsg("GetPosition")
                    logger.debug("Conex: Asked position. Waiting for response")
                    returnedmessage = self.socket.receive()
                    logger.debug("Conex: Received response: {}".format(returnedmessage))
                    curPos = float(returnedmessage)
                    while(abs(i.SetPos.value - curPos) > i.Threshold.value):  #loop until the error is less than threshold
                        time.sleep(0.1)
                        self.socket.sendmsg("GetPosition")
                        returnedmessage = self.socket.receive()
                        curPos = float(returnedmessage)
            except Exception as e:
                logger.error('Problem setting Conex positions, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError
