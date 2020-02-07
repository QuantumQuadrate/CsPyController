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

from atom.api import Bool, Str, Member, Int, Float
from instrument_property import Prop, FloatProp, IntProp, ListProp, BoolProp, StrProp
from cs_instruments import Instrument
from analysis import Analysis
import TCP
from cs_errors import PauseError
import time
import subprocess
import sys
sys.path.append(r'C:\Program Files\Newport\MotionControl\CONEX-CC\Python')
sys.path.append(r'C:\Program Files (x86)\Newport\MotionControl\CONEX-CC\Python')
from ConexCC_Functions import *

class Conex(Prop):
    SetPos = Member()
    Vel = Member()
    enableVel = Bool()
    IDString = Member()
    Threshold = Member()
    #port = Int()
    #socket = Member()
    #IP = Str()
    CC = Member()
    address = Int(1)
    displayFlag = Int(0)
    curpos = Float(0)
    enable = Bool()
    isInitialized = Bool(False)

    def __init__(self, name, experiment, description=''):
        super(Conex, self).__init__(name, experiment, description)
        self.IDString = StrProp('IDString', experiment, 'Instrument Key','0')
        self.SetPos = FloatProp('SetPos', experiment, 'Set position (mm)','0')
        self.Vel = FloatProp('Vel', experiment, 'Velocity (mm/s)','0')
        self.Threshold = FloatProp('PositionThreshold', experiment, 'Threshold for Position (mm)','0')
        self.properties += ['SetPos', 'enableVel', 'Vel', "IDString", 'Threshold', 'enable']


    def initialize(self):
        #self.socket = TCP.CsClientSock(self.IP, self.port)
        logger.warning('CONEX IDString: {}'.format(self.IDString.value))
        #msg = 'Init,{}'.format(self.IDString.value)
        #self.socket.sendmsg(msg)
        #logger.warning("CONEX: Sent initialization message, waiting for response")
        #returnedmessage = self.socket.receive()
        #logger.warning("CONEX: Received response: {}".format(returnedmessage))
        CC = ConexCC()
        ret = CC.OpenInstrument(self.IDString.value)
        self.CC = CC
        if ret==0:
            if CONEXCC_HomeSearch(self.CC,self.address,self.displayFlag) != 0:
                return "Failed to home Conex: ID {}, retcode {}".format(self.IDString.value,ret)
            CONEXCC_WaitEndOfHomeSearch(self.CC,self.address)
            return "Success"
        else:
            return "Failed to open Conex: ID {}, retcode {}".format(self.IDString.value, ret)

    def update(self):
        if (self.enableVel == False):
            logger.warning('CONEX position: {}'.format(self.SetPos.value))
            #msg = 'SetPosition,{}'.format(self.SetPos.value)
            self.CC.PA_Set(self.address,self.SetPos.value, "")
        else:
            #msg = 'SetPositionVelocity,{},{}'.format(self.SetPos.value,self.Vel.value)
            self.CC.VA_Set(self.address,self.Vel.value, "")
            self.CC.PA_Set(self.address,self.SetPos.value, "")
        returnValue, position = CONEXCC_GetPosition(self.CC,self.address, self.displayFlag)
        if returnValue != 0:
            logger.error("Failed to get CONEX position: ID {}, retcode {}".format(self.IDString.value,returnValue))
        self.curpos = position
        #logger.debug("Conex: About to send update to CONEX server")
        #self.socket.sendmsg(msg)
        #logger.debug("Conex: Sent update to CONEX server. About to ask position")
        #self.socket.sendmsg("GetPosition")
        #logger.debug("Conex: Asked position. Waiting for response")
        #returnedmessage = self.socket.receive()
        #logger.debug("Conex: Received response: {}".format(returnedmessage))
        return position

    def launchServer(self):
        #subprocess.Popen(["C:\\Windows\\System32\\cmd.exe","/C","..\\csharp\\CONEX_Server\\bin\\Debug\\CONEX-CC-CSharp-Server.exe",str(self.port)], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return

class Conexes(Instrument):
    version = '2015.06.22'
    #IP = Str()
    #port = Int()
    motors = Member()
    #socket = Member()

    def __init__(self, name, experiment, description=''):
        super(Conexes, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual CONEX-CC stages', listElementType=Conex,
                               listElementName='motor')
        self.properties += ['version', 'motors']



    def preExperiment(self, hdf5):
        """Open the TCP socket"""
        if self.enable:
            for i in self.motors:
                if i.enable:
                    try:
                        #i.IP = self.IP
                        returnedmessage = i.initialize()
                        i.isInitialized = True

                        if (returnedmessage != "Success"):
                            logger.error('Problem initializing Conex: \n{}\n'.format(returnedmessage))
                            i.isInitialized = False
                            return PauseError
                    except Exception as e:
                        logger.error('Problem initializing Conex: \n{}\n{}\n'.format(i.IDString.value,e))
                        i.isInitialized = False
                        return PauseError
            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True


    def postMeasurement(self, callbutt, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self, hdf5):
        #if self.enable:
        #    for i in self.motors:
        #        i.socket.close()
        return

    def preIteration(self, iterationresults, hdf5):
        """
        Every iteration, send the motors updated positions.
        """
        if self.enable:
            msg = ''


            for i in self.motors:
                if i.enable:
                    try:
                        if not i.isInitialized:
                            try:
                                #i.IP = self.IP
                                returnedmessage = i.initialize()
                                i.isInitialized = True

                                if (returnedmessage != "Success"):
                                    logger.error('Problem initializing Conex: \n{}\n'.format(returnedmessage))
                                    i.isInitialized = False
                                    return PauseError
                            except Exception as e:
                                logger.error('Problem initializing Conex: \n{}\n{}\n'.format(i.IDString.value,e))
                                i.isInitialized = False
                                return PauseError
                        i.update()
                        # send update to the conex server

                        loopCount=0
                        loopThreshold=150
                        while(abs(i.SetPos.value - i.curpos) > i.Threshold.value and loopCount < loopThreshold):  #loop until the error is less than threshold
                            time.sleep(0.1)
                            #i.socket.sendmsg("GetPosition")
                            #returnedmessage = i.socket.receive()
                            returnValue, position = CONEXCC_GetPosition(i.CC,i.address, i.displayFlag)
                            if returnValue != 0:
                                logger.error("Failed to get CONEX position: ID {}, retcode {}".format(i.IDString.value,returnValue))
                            i.curpos = position
                            loopCount = loopCount+1
                        if (loopCount>=loopThreshold):
                            logger.warning("Conex: Did not converge to correct position in 10 seconds. Is the threshold too small?")
                        else:
                            logger.debug("Conex: Converged to position.")
                    except Exception as e:
                        logger.error('Problem setting Conex positions,:\n{}\n{}\n'.format(i.IDString.value, e))
                        #i.socket.close()
                        i.isInitialized = False
                        raise PauseError

    def start(self):
        self.isDone = True
        return

    def update(self):
        self.preIteration(0,0)
        return

    def initialize(self):
        self.preExperiment(0)
