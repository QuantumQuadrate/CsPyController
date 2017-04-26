"""FakeInstrument.py
Part of the AQuA Cesium Controller software package

author=Matthew Ebert
created=2017-04-25

This instrument generates random data for testing purposes.
"""

from __future__ import division
__author__ = 'Matthew Ebert'
import logging
logger = logging.getLogger(__name__)

from numpy.random import random_sample, rand

from cs_instruments import Instrument

class Embezzletron(Instrument):
    version = '2017.04.25'

    def __init__(self, name, experiment, description=''):
        super(Embezzletron, self).__init__(name, experiment, description)
        self.enable = False

    def start(self):
        self.isDone = True

    def generateData(self):
        return random_sample(5)

    def generateArray(self):
        return rand(7,7)

    def writeResults(self, hdf5):
        try:
            hdf5['embezzletron/dataList'] = self.generateData()
            hdf5['embezzletron/dataArray'] = self.generateArray()

        except Exception as e:
            logger.error('in embezzletron.writeResults() while making up data\n{}'.format(e))
            raise PauseError