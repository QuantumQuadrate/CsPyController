from __future__ import division

"""
aerotech.py

part of the CsPyController package for AQuA experiment control by Martin Lichtman

Handles sending global variable updates to the Aerotech Ensemble translation stage.
This python code sends commands via TCP to a server running in C#, also in this package.
The C# server then uses the .NET assembly provided by Aerotech to talk to the Ensemble driver.

created = 2015.06.22
modified >= 2015.06.22
"""

__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Bool, Member, Float
from instrument_property import FloatProp, StrProp
from cs_instruments import Instrument
from cs_errors import PauseError
import NewportStageController as newportcontroller
import time





class NewportStage(Instrument):
    version = '2016.12.21'
    setposition = Member()
    allow_evaluation = Bool(True)
    gui = Member()
    nport = Member()
    comport = Member()
    velocity = Member()
    command=Member()
    mypos = Float()
    axis = Member()
    statusmeasurement = Bool(True)

    def __init__(self, name, experiment, description=''):
        super(NewportStage, self).__init__(name, experiment, description)
        self.setposition = FloatProp('setposition', experiment, 'Set Position (mm)','0')
        self.comport = StrProp('comport',experiment,'COM port','COM6')
        self.axis = StrProp('axis',experiment,'Axis','X')
        self.velocity = FloatProp('velocity',experiment,'Velocity (mm/s)','10')
        self.command = StrProp('command',experiment,'Command to send','')
        self.properties += ['setposition', 'comport', 'velocity', 'axis',
                            'version','statusmeasurement']

    def initialize(self):
        if self.nport is not None:
            #print "Deleting Newport controller"
            del self.nport
        if self.enable and not self.isInitialized:
            self.nport = newportcontroller.Newport(self.comport.value, self.axis.value)
            self.isInitialized = True
            # if self.nport.test_port():
            #    print "Port is initialized, Axis = {}.".format(self.axis.value)
            #    self.isInitialized = True
            # else:
            #    print "Wrong Port try again"
            #    self.isInitialized = False

    def start(self):
        self.isDone = True
            
    def update(self):
        if self.enable:
            self.moveStage()
        return

    def moveStage(self,recurse=0):
        maxrecurse=3
        if recurse > maxrecurse:
            logger.error("Newport stage position not reached in 10 seconds")
            logger.error("Set Position: {} mm, observed position: {} mm".format(self.setposition.value,self.mypos))
            raise PauseError
        if not self.isInitialized:
            self.initialize()
        self.nport.moveAbs(self.setposition.value*1000)
        done=self.nport.status()
        loopcounter=0
        while done != self.axis.value + 'D':
            done = self.nport.status()
            logger.info('Status: {}\n'.format(done))
            loopcounter += 1
            # controller sometimes gets confused,
            # resulting in it returning B continuously.
            # If this happens, reset the driver and try again.
            if loopcounter > 10:
                self.isInitialized = False
                self.moveStage(recurse=recurse+1)
        logger.info('Status: {}\n'.format(done))
        self.mypos = self.whereAmI()
        loopcounter=0
        maxloops=3
        while loopcounter < maxloops and abs(self.mypos-self.setposition.value) > .001:
            time.sleep(.05)
            self.mypos = self.whereAmI()
            loopcounter+=1
        if loopcounter >=maxloops:
            logger.warning('Newport stage did not converge. Attempting command again.')
            self.moveStage(recurse=recurse+1)   #if it doesn't converge, try sending the command again.


    def updateaxis(self):
        if not self.isInitialized:
            self.initialize()
        else:
            self.nport.setaxis(self.axis.value)
            
    def checkCurrentPosition(self):
        self.mypos = self.whereAmI()

    def whereAmI(self):
        return self.nport.whereAmI()/1000

    def writeResults(self, hdf5):
        if self.enable and self.statusmeasurement:
            self.mypos = self.whereAmI()
        return
        
    def calibrate(self):
        if not self.isInitialized:
            self.initialize()
        self.nport.calibrateStage()

    def findcenter(self):
        if not self.isInitialized:
            self.initialize()
        self.nport.findCenter()
    
    def home(self):
        if not self.isInitialized:
            self.initialize()
        self.nport.home()
        
    def setvelocity(self):
        if not self.isInitialized:
            self.initialize()
        self.nport.setVelocity(self.velocity.value*1000)

    def sendSerialCommand(self):
        self.nport.WriteThenPrint(self.command.value)