"""Counter.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2013-10-19

This file holds everything to model a National Instruments DAQmx counter.  It communicated to LabView via the higher up LabView class.
"""


from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError

from cs_instruments import Instrument

class Counter(Instrument):
    def evaluate(self):
        if self.experiment.allow_evaluation:
            logger.debug('Counter.evaluate()')
            return super(Counter, self).evaluate()