"""Counter.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2013-10-19
modified>=2015-05-11

This file holds everything to model a National Instruments DAQmx counter.
It communicated to LabView via the higher up LabView(Instrument) class.
Saving of returned data is handled in the LabView class.
"""


from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from atom.api import Str, Float, Typed
from cs_instruments import Instrument
from instrument_property import Prop, ListProp

class Counters(Instrument):
    version = '2015.05.11'
    counters = Typed(ListProp)

    def __init__(self, name, experiment, description=''):
        super(Counters, self).__init__(name, experiment, description)
        # start with a blank list of counters
        self.counters = ListProp('counters', experiment, listElementType=Counter, listElementName='counter')
        self.properties += ['version', 'counters']

class Counter(Prop):
    """ Each individual counter has a field for the signal source, clock source, and clock rate (in Hz, used only for
    internal clocking).
    """

    counter_source = Str()
    clock_source = Str()
    clock_rate = Float()

    def __init__(self, name, experiment, description=''):
        super(Counter, self).__init__(name, experiment, description)
        self.properties += ['counter_source', 'clock_source', 'clock_rate']
