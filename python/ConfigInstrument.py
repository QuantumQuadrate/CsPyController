"""FakeInstrument.py
Part of the AQuA Cesium Controller software package

author=Matthew Ebert
created=2017-04-25

This instrument generates random data for testing purposes.
"""

from __future__ import division
from atom.api import Member
from numpy.random import random_sample, randint
from cs_instruments import Instrument
from instrument_property import IntProp
from cs_errors import PauseError
import time

__author__ = 'Matthew Ebert'
import logging
logger = logging.getLogger(__name__)


class Embezzletron(Instrument):
    version = '2017.04.25'
    shotsPerMeasurement = Member()

    def __init__(self, name, experiment, description=''):
        super(Embezzletron, self).__init__(name, experiment, description)
        self.enable = False

    def initialize(self):
        pass

    def start(self):
        self.isDone = True

    def writeResults(self, hdf5):
        pass

    def toHDF5(self, hdf):
        pass

    def fromHDF5(self, hdf):
        pass
