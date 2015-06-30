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

import numpy as np

import traceback
from atom.api import Str, Float, Typed, Member, Bool, Int
from cs_instruments import Instrument
from instrument_property import Prop, ListProp
from analysis import AnalysisWithFigure

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


class CounterAnalysis(AnalysisWithFigure):
    counter_array = Member()
    binned_array = Member()
    update_lock = Bool(False)
    enable = Bool(True)
    drops = Int(3)
    bins = Int(25)

    def __init__(self, name, experiment, description=''):
        super(CounterAnalysis, self).__init__(name, experiment, description)
        self.properties += ['enable']


    def preExperiment(self, experimentResults):
        self.counter_array = None
        self.binned_array = None
        #measurements x bins

    def analyzeMeasurement(self, measurementResults, iterationResults, experimentResults):
        if self.enable:
                self.binned_array = np.array([self.counter_array[: ,self.drops-1:self.drops+self.bins].sum(1),
                                              self.counter_array[: ,2*self.drops+self.bins:].sum(1)])
        self.updateFigure()


    def updateFigure(self):
        if self.enable:
            if not self.update_lock:
                try:
                    self.update_lock = True

                    # There are two figures in an AnalysisWithFigure.  Draw to the offscreen figure.
                    fig = self.backFigure
                    # Clear figure.
                    fig.clf()

                    #make one plot
                    ax = fig.add_subplot(221)
                    # Drop first 3 bins

                    ax.bar(np.arange(len(self.counter_array[-1, self.drops:])), self.counter_array[-1, self.drops:])
                    ax.set_title('Shot: {}'.format(len(self.counter_array)))#Singlt shot

                    ax = fig.add_subplot(222)
                    ax.bar(np.arange(len(self.counter_array[-1, self.drops:])), self.counter_array[:, self.drops:].mean(0))
                    ax.set_title('Iteration average') #Average over all shots/iteration

                    ax = fig.add_subplot(223)
                    ax.plot(self.binned_array.transpose(),'.')



                    ax.legend(['shot 1', 'shot 2'], fontsize='small', loc=0)
                    ax.set_title('Binned Data')

                    ax = fig.add_subplot(224)
                    ax.hist(self.binned_array[0], bins=40, histtype='step')
                    ax.hist(self.binned_array[1], bins=40, histtype='step')


                    super(CounterAnalysis, self).updateFigure()

                except Exception as e:
                    logger.warning('Problem in RetentionGraph.updateFigure()\n{}\n{}\n'.format(e, traceback.format_exc()))
                finally:
                    self.update_lock = False

