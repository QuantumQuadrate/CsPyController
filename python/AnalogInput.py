"""AnalogInput.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2014-08-19
modified>=2014-08-19

This file holds everything needed to set up a finite acquisition of a fixed number of data points during the
experiment from a National Instruments DAQmx card.
It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Typed
from instrument_property import BoolProp, FloatProp, StrProp, IntProp
from cs_instruments import Instrument


class AnalogInput(Instrument):
    version = '2014.08.19'
    sample_rate = Typed(FloatProp)
    source = Typed(StrProp)
    samples_per_measurement = Typed(IntProp)
    waitForStartTrigger = Typed(BoolProp)
    triggerSource = Typed(StrProp)
    triggerEdge = Typed(StrProp)

    def __init__(self, experiment):
        super(AnalogInput, self).__init__('AnalogInput', experiment)
        self.sample_rate = FloatProp('sample_rate', experiment, '', '1000.0')
        self.source = StrProp('source', experiment, '', '"PXI1Slot6/ai0:15"')
        self.samples_per_measurement = IntProp('samples_per_measurement', experiment, '', '1')
        self.waitForStartTrigger = BoolProp('waitForStartTrigger', experiment, '', 'True')
        self.triggerSource = StrProp('triggerSource', experiment, '', '"/PXI1Slot6/PFI0"')
        self.triggerEdge = StrProp('triggerEdge', experiment, '"Rising" or "Falling"', '"Rising"')
        self.properties += ['version', 'sample_rate', 'source', 'samples_per_measurement', 'waitForStartTrigger',
                            'triggerSource', 'triggerEdge']
