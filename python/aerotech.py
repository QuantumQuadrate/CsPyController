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
from instrument_property import Prop, FloatProp, IntProp, ListProp, EvalProp
from cs_instruments import Instrument
from analysis import Analysis
from cs_errors import PauseError
import sys, os
print os.getcwd()
sys.path.append(r'{}\..\csharp\Aerotech_Ensemble_Server'.format(os.getcwd()))
print sys.path
import clr
clr.AddReference("Aerotech.Common")
clr.AddReference("Aerotech.Ensemble")
from Aerotech.Ensemble import *
from Aerotech.Common import *




class Aerotech(Prop):
    '''Xi = Member()
    Xend = Member()
    Xvmx = Member()
    Xamx = Member()
    Zi = Member()
    Zend = Member()
    Zvmx = Member()
    Zamx = Member()
    XretTrig = Member()'''

    globals = Member()
    allow_evaluation = Bool(True)
    gui = Member()
    myController = Member()

    def __init__(self, name, experiment, description=''):
        super(Aerotech, self).__init__(name, experiment, description)
        '''self.Xi = FloatProp('Xi', experiment, 'Initial X position (mm)','0')
        self.Xend = FloatProp('Xend', experiment, 'Final X position (mm)','0')
        self.Xvmx = FloatProp('Xvmx', experiment, 'Max X velocity (mm/s)','0')
        self.Xamx = FloatProp('Xend', experiment, 'Max X acceleration (mm/s^2)','0')
        self.Zi = FloatProp('Zi', experiment, 'Initial Z position (mm)','0')
        self.Zend = FloatProp('Zend', experiment, 'Final Z position (mm)','0')
        self.Zvmx = FloatProp('Zvmx', experiment, 'Max Z velocity (mm/s)','0')
        self.Zamx = FloatProp('Zend', experiment, 'Max Z acceleration (mm/s^2)','0')
        self.XretTrig = IntProp('XretTrig', experiment, 'X Trig Return?','0')'''
        self.globals = ListProp('globals', experiment, listElementType=FloatProp,
                                             listElementName='global')
        self.properties += ['globals']

    def update(self):
        for i,k in enumerate(self.globals):
            self.myController.Commands.Register.WriteDoubleGlobal(i,k.value)
        #integer globals go here if needed
        self.myController.Parameters.System.User.UserInteger0.Value = 1

    def waitForGlobals(self):
        self.myController.Parameters.System.User.UserInteger0.Value = -1

class Aerotechs(Instrument,Analysis):
    version = '2015.06.22'
    IP = Str()
    port = Int()
    motors = Member()
    socket = Member()
    OneAerotech=Member()

    def __init__(self, name, experiment, description=''):
        super(Aerotechs, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Aerotech stages', listElementType=Aerotech,
                               listElementName='motor')
        self.OneAerotech = Aerotech('OneAerotech',experiment,'One Aerotech Ensemble')
        self.properties += ['version', 'IP', 'port', 'motors','OneAerotech']

    def launchServer(self):
        #subprocess.Popen(["C:\\Windows\\System32\\cmd.exe","/C","..\\csharp\\Aerotech_Ensemble_Server\\bin\\Debug\\Ensemble Console Example CSharp.exe"], creationflags=subprocess.CREATE_NEW_CONSOLE)
        return

    def preExperiment(self, hdf5):
        """Open the TCP socket"""
        if self.enable:
            self.OneAerotech.myController = Controller.Connect()[0]
            logger.debug("Aerotech: preExperiment: sending WaitForGlobals")
            self.OneAerotech.waitForGlobals()
            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True

    def postMeasurement(self, callback, measurementresults, iterationresults, hdf5):
        super(Aerotechs,self).postMeasurement(callback, measurementresults,iterationresults,hdf5)
        return

    def postIteration(self, iterationresults, hdf5):
        if self.enable:
            self.OneAerotech.waitForGlobals()
        super(Aerotechs,self).postIteration(iterationresults,hdf5)
        return

    def postExperiment(self, hdf5):
        return

    def finalize(self,hdf5):
        return

    def preIteration(self, iterationresults, hdf5):
        """
        Every iteration, send the motors updated positions.
        """
        #print "Running aerotech preIteration"
        if (not self.isInitialized):
            self.preExperiment(hdf5)
        if self.enable:
            msg = ''
            try:
                self.OneAerotech.update()
            except Exception as e:
                logger.error('Problem setting Aerotech globals, closing socket:\n{}\n{}\n'.format(msg, e))
                self.isInitialized = False
                raise PauseError

    def parUpdate(self):
        """
        Passes WaitForGlobals value update and then runs the preiteration step
        :return:
        """
        self.preIteration(0,0)
        self.OneAerotech.waitForGlobals()
        self.preIteration(0,0)
        return

    def start(self):
        self.isDone = True
        return

    def update(self):
        self.preIteration(0,0)
        return

    def initialize(self):
        self.preExperiment(0)
