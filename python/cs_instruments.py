#cs_instruments.py
#author = Martin Lichtman
#created = 2013-07-10
#modified >= 2013-07-10

#This file is part of the Cesium Control program designed by Martin Lichtman in 2013 for the AQuA project.
#It contains classes that represent instruments

from cs_errors import PauseError, setupLog
logger = setupLog(__name__)

from atom.api import Bool, Member
from instrument_property import Prop
    
class Instrument(Prop):
    isInitialized = Bool()
    isDone = Bool()
    instruments = Member()
    data = Member()
    
    def __init__(self, name, experiment, description=''):
        super(Instrument, self).__init__(name, experiment, description)
        self.instruments = []
        self.isInitialized = False
        self.isDone = True
        self.data = []

    def update(self):
        """Sends current settings to the instrument.  This function is run at the beginning of every new iteration.
        Does not explicitly call evaluate, to avoid duplication of effort.
        All calls to evaluate should already have been accomplished."""
       
        for i in self.instruments:
            i.update() #call update for any sub-instrument

        #the details of sending to each instrument must be handled in a subclass
        #first call super(subclass,self).update() to call this method
        #then do the hardware update, probably involving sending the toXML string via TCP/IP
    
    def start(self):
        """Enables the instrument to begin a measurement.  Sent at the beginning of every measurement.
        Actual output or input from the measurement may yet wait for a signal from another device."""
        pass
    
    def stop(self):
        """Stops output as soon as possible.  This is not run during the course of a normal instrument."""
        pass
    
    def initialize(self):
        """Sends initialization commands to the instrument"""
        for i in self.instruments:
            i.initialize()
        self.isInitialized = True
