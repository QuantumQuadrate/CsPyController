"""functional_waveforms.py
Part of the AQuA Cesium Controller software package

author=Martin Lichtman
created=2015-05-19
modified>=2015-05-019

This file holds text files which specify the waveform timing for HSDIO, DAQmx DIO, and DAQmx AO.
Waveforms are specified as python functions.  Every waveform function must take in the absolute time
for the waveform to begin, and must return the absolute time when the waveform ends.  In this way, the length of each
waveform can easily be used to synchronize all three of these instruments.
This file holds everything needed to model the high speed digital output from the National Instruments HSDIO card.  It communicates to LabView via the higher up LabView(Instrument) class.
"""

from __future__ import division
__author__ = 'Martin Lichtman'
import logging
logger = logging.getLogger(__name__)

from cs_errors import PauseError
import cs_evaluate


class FunctionalWaveforms(Instrument):
    """A virtual instrument that specifies the timing for HSDIO, DAQmx DIO, and DAQmx AO."""
    version = '2015.05.19'

    text = Str()  # a text string that holds all the waveforms
    instrument_list = Str()  # a string giving a list of the instruments that should be made available to this analysis

    def __init__(self, name, experiment, description=''):
        super(FunctionalWaveforms, self).__init__(name, experiment, description)
        self.properties += ['version', 'instrument_list','text']

    def evaluate(self):
        if self.enable and self.experiment.allow_evaluation:
            logger.debug('FunctionalWaveforms.evaluate()')

            localvars = self.experiment.vars.copy()
            localvars.update({'experiment': self.experiment})
            cs_evaluate.execWithDict(self.text, localvars)

            return super(FunctionalWaveforms, self).evaluate()
