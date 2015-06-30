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

from atom.api import Bool, Str, Member, Int
from instrument_property import Prop, FloatProp, IntProp, ListProp
from cs_instruments import Instrument
import TCP
from cs_errors import PauseError

class Aerotech(Prop):
    Xi = Member()
    Xend = Member()
    Xvmx = Member()
    Xamx = Member()
    Zi = Member()
    Zend = Member()
    Zvmx = Member()
    Zamx = Member()
    XretTrig = Member()

    def __init__(self, name, experiment, description=''):
        super(Aerotech, self).__init__(name, experiment, description)
        self.Xi = FloatProp('Xi', experiment, 'Initial X position (mm)','0')
        self.Xend = FloatProp('Xend', experiment, 'Final X position (mm)','0')
        self.Xvmx = FloatProp('Xvmx', experiment, 'Max X velocity (mm/s)','0')
        self.Xamx = FloatProp('Xend', experiment, 'Max X acceleration (mm/s^2)','0')
        self.Zi = FloatProp('Zi', experiment, 'Initial Z position (mm)','0')
        self.Zend = FloatProp('Zend', experiment, 'Final Z position (mm)','0')
        self.Zvmx = FloatProp('Zvmx', experiment, 'Max Z velocity (mm/s)','0')
        self.Zamx = FloatProp('Zend', experiment, 'Max Z acceleration (mm/s^2)','0')
        self.XretTrig = IntProp('XretTrig', experiment, 'X Trig Return?','0')
        self.properties += ['Xi', 'Xend', 'Xvmx', 'Xamx', 'Zi', 'Zend', 'Zvmx', 'Zamx', 'XretTrig']

    def update(self):
        return 'UpdateGlobals,{},{},{},{},{},{},{},{},{}'.format(self.Xi.value, self.Xend.value, self.Xvmx.value, self.Xamx.value ,self.Zi.value, self.Zend.value, self.Zvmx.value, self.Zamx.value, self.XretTrig.value)


class Aerotechs(Instrument):
    version = '2015.06.22'
    IP = Str()
    port = Int()
    motors = Member()
    socket = Member()

    def __init__(self, name, experiment, description=''):
        super(Aerotechs, self).__init__(name, experiment, description)
        self.motors = ListProp('motors', experiment, 'A list of individual Aerotech stages', listElementType=Aerotech,
                               listElementName='motor')
        self.properties += ['version', 'IP', 'port', 'motors']

    def preExperiment(self, hdf5):
        """Open the TCP socket"""
        if self.enable:
            self.socket = TCP.CsClientSock(self.IP, self.port)
            self.socket.sendmsg("WaitForGlobals")
            # TODO: add here some sort of communications check to see if it worked

            self.isInitialized = True

    def postMeasurement(self, measurementresults, iterationresults, hdf5):
        return

    def postIteration(self, iterationresults, hdf5):
        self.socket.sendmsg("WaitForGlobals")
        return

    def postExperiment(self, hdf5):
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
                    # send update to the aerotech server
                    self.socket.sendmsg(msg)
            except Exception as e:
                logger.error('Problem setting Aerotech globals, closing socket:\n{}\n{}\n'.format(msg, e))
                self.socket.close()
                self.isInitialized = False
                raise PauseError
