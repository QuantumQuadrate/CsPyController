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

from atom.api import Bool, Str, Member, Int, Float
from instrument_property import Prop, FloatProp, IntProp, ListProp, EvalProp, StrProp
from cs_instruments import Instrument
from analysis import Analysis
import TCP
from cs_errors import PauseError
import subprocess
import NewportStageController as newportcontroller
import time





class NewportStage(Instrument):
    version = '2016.12.21'
    setposition = Member()
    allow_evaluation = Bool(True)
    gui = Member()
    nport = Member()
    comport = Member()
    mypos = Float()

    def __init__(self, name, experiment, description=''):
        super(NewportStage, self).__init__(name, experiment, description)
        self.setposition = FloatProp('setposition', experiment, 'Set Position (mm)','0')
        self.comport = StrProp('comport',experiment,'COM port','COM6')
        self.properties += ['setposition','comport']

    def initialize(self):
        if self.enable and not self.isInitialized:
            self.nport = newportcontroller.Newport(self.comport.value)
            self.isInitialized = True

    def update(self):
        if self.enable:
            self.moveStage()
        return

    def moveStage(self):
        if not self.isInitialized:
            self.nport = newportcontroller.Newport(self.comport.value)
            self.isInitialized = True
        self.nport.moveAbs(self.setposition.value*1000)
        self.mypos = self.whereAmI()
        loopcounter=0
        while loopcounter < 100 and abs(self.mypos-self.setposition.value) > .001:
            time.sleep(.1)
            self.mypos = self.whereAmI()
            loopcounter+=1
        if loopcounter >= 100:
            logger.error("Newport stage position not reached in 10 seconds")
            logger.error("Set Position: {} mm, observed position: {} mm".format(self.setposition.value,mypos))
            raise PauseError

    def whereAmI(self):
        return self.nport.whereAmI()/1000

    def writeResults(self, hdf5):
        if self.enable:
            self.mypos = self.whereAmI()
        return


