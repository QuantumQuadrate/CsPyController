"""functional_waveforms.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2015-05-19
modified>=2015-05-019

This file holds text files which specify the waveform timing for HSDIO, DAQmx DIO, and DAQmx AO.
Waveforms are specified as python functions.  Every waveform function must take in the absolute time
for the waveform to begin, and must return the absolute time when the waveform ends.  In this way, the length of each
waveform can easily be used to synchronize all three of these instruments.

In practice the functionality of this instrument is exactly the same as the dependent variables,
except that the resulting definitions will not be saved into the HDF5 file.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError
import cs_evaluate
from analysis import AnalysisWithFigure
from instrument_property import Prop


class FunctionalWaveforms(Prop):
    """A virtual instrument that specifies the timing for HSDIO, DAQmx DIO, and DAQmx AO."""
    version = '2015.05.19'

    text = Str()  # a text string that holds all the waveforms

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveforms, self).__init__(name, experiment, description)
        self.properties += ['version', 'text']

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('FunctionalWaveforms.evaluate()')

            localvars = self.experiment.vars.copy()
            cs_evaluate.execWithDict(self.text, localvars)

            return super(FunctionalWaveforms, self).evaluate()

class FunctionalWaveformGraph(AnalysisWithFigure):
    """
    This analysis is not set up to be called after measurements or iterations.  It is set up to update on evaluate().
    """

    labels = Member()
    spans = Member()

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveformGraph, self).__init__(name, experiment, description)
        self.properties += ['enable']

    def __init__(self):
        self.labels = []

    def label(self, time, text):
        self.labels += [(time, text)]

    def span(self, t1, t2, text):
        self.spans += [(t1, t2, text)]

    def evaluate(self):
        # update the plot

        # make the digital plots

        # make the analog plots

        # clear the label lists
        self.labels = []
        self.spans = []
