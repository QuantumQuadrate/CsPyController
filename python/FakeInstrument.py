"""FakeInstrument.py
Part of the AQuA Cesium Controller software package

author=Matthew Ebert
created=2017-04-25

This instrument generates random data for testing purposes.
"""

from __future__ import division
from atom.api import Typed
from numpy.random import random_sample, randint
import numpy as np
from cs_instruments import Instrument
from instrument_property import IntProp, FloatProp, FloatRangeProp
from cs_errors import PauseError
import time

__author__ = 'Matthew Ebert'
import logging
logger = logging.getLogger(__name__)


class Embezzletron(Instrument):
    version = '2017.04.25'
    shotsPerMeasurement = Typed(IntProp)
    photoelectronScaling = Typed(FloatProp)
    exposureTime = Typed(FloatRangeProp)

    def __init__(self, name, experiment, description=''):
        super(Embezzletron, self).__init__(name, experiment, description)
        self.enable = self.experiment.Config.config.getboolean(
            'DEV',
            'EnableFakeData'
        )
        self.shotsPerMeasurement = IntProp(
            'shotsPerMeasurement',
            experiment,
            'number of expected shots',
            '2'
        )
        self.shotsPerMeasurement.value = 2

        self.photoelectronScaling = FloatProp(
            'photoelectronScaling',
            experiment,
            'photoelectron scaling',
            '1'
        )
        self.exposureTime = FloatRangeProp(
            'exposureTime',
            experiment,
            'exposure time (seconds)',
            low=0.000001,
            high=7200
        )
        self.exposureTime.value = 0.05

    def initialize(self):
        # time.sleep(0.01)
        pass

    def start(self):
        self.isDone = True

    def generateData(self):
        return random_sample(5)

    def generateArray(self):
        image_shape = (100, 100)
        bg = randint(10, size=image_shape)
        rows = self.experiment.ROI_rows
        cols = self.experiment.ROI_columns
        sites = rows * cols
        x0 = 10
        y0 = 10
        grid = np.indices(bg.shape)
        xy0 = np.array([[[x0]], [[y0]]])
        sigma = np.array([[[3]], [[3]]])
        spots = np.empty((sites, image_shape[0], image_shape[1]))
        spacing = 15
        i = 0
        amp = 5
        atom = randint(2, size=sites)
        for r in range(rows):
            for c in range(cols):
                xy0i = xy0 + np.array([[[r]], [[c]]]) * spacing
                spots[i] = self.gaussian(amp, sigma, xy0i, grid)
                if atom[i]:
                    bg = np.add(bg, spots[i])
                i += 1
        return bg

    def generateShots(self, hdf5):
        time.sleep(0.01)
        for i in range(self.shotsPerMeasurement.value):
            hdf5['embezzletron/shots/' + str(i)] = self.generateArray()

    def writeResults(self, hdf5):
        try:
            hdf5['embezzletron/dataList'] = self.generateData()
            hdf5['embezzletron/dataArray'] = self.generateArray()
            self.generateShots(hdf5)

        except Exception as e:
            msg = 'in embezzletron.writeResults() while making up data\n{}'
            logger.error(msg.format(e))
            raise PauseError

    def normal_gaussian(self, a, xy):
        return a * np.exp(-0.5 * (np.sum(xy**2, axis=0)))

    def elliptical_gaussian(self, a, w, xy):
        return self.normal_gaussian(a, xy / w)

    def gaussian(self, a, w, xy0, xy):
        return self.elliptical_gaussian(a, w, xy - xy0)
