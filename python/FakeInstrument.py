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
        self.enable = True
        self.shotsPerMeasurement = IntProp(
                                    'shotsPerMeasurement',
                                    experiment,
                                    'number of expected shots', '2'
                                )
        self.shotsPerMeasurement.value = 2

    def initialize(self):
        # time.sleep(0.01)
        pass

    def start(self):
        self.isDone = True

    def generateData(self):
        return random_sample(5)

    def generateArray(self):
        return randint(10, size=(5, 5))

    def generateShots(self, hdf5):
        time.sleep(0.1)
        for i in range(self.shotsPerMeasurement.value):
            hdf5['embezzletron/shots/'+str(i)] = self.generateArray()

    def writeResults(self, hdf5):
        try:
            hdf5['embezzletron/dataList'] = self.generateData()
            hdf5['embezzletron/dataArray'] = self.generateArray()
            self.generateShots(hdf5)

        except Exception as e:
            msg = 'in embezzletron.writeResults() while making up data\n{}'
            logger.error(msg.format(e))
            raise PauseError
